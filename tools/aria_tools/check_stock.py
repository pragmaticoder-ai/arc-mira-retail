"""check_stock — SPEC-ARIA-04.

Real-time stock for a product at a store. Surfaces active discounts so ARIA
can mention them (ARIA system prompt). Lists alternative stores with stock.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.logger import get_logger
from tools.shared.rate_limit import limiter

logger = get_logger("aria.check_stock")
router = APIRouter()


_STORE_NAMES = {
    "dubai_marina_01": ("MIRA Dubai Marina", 0.0),
    "jbr_01": ("MIRA JBR", 1.2),
    "al_barsha_01": ("MIRA Al Barsha", 8.5),
}


def check_stock(product_id: str, store_id: str) -> dict:
    """
    Checks real-time stock for a specific product at a specific store.
    Returns available, quantity, aisle_ref, discount info, and
    alternative_stores. Call for every item before confirming it in the cart.
    """
    if not (product_id or "").strip():
        return error("VALIDATION_ERROR", "product_id is empty")
    if not (store_id or "").strip():
        return error("VALIDATION_ERROR", "store_id is empty")

    db = get_alloydb()
    # Does this product exist anywhere? (NOT_FOUND only if unknown product)
    at_store = db.get_product_at_store(product_id, store_id)
    exists_anywhere = at_store is not None or db.get_product(product_id) is not None
    if not exists_anywhere:
        return error("NOT_FOUND", f"product {product_id} not found")

    quantity = at_store["stock_quantity"] if at_store else 0
    available = quantity > 0

    # Alternative stores only when unavailable here (SPEC-ARIA-04 §4).
    alternatives: list[dict] = []
    if not available:
        for row in db.list_product_across_stores(product_id, exclude_store_id=store_id):
            if row["stock_quantity"] <= 0:
                continue
            name, dist = _STORE_NAMES.get(row["store_id"], (row["store_id"], 0.0))
            alternatives.append(
                {
                    "store_id": row["store_id"],
                    "store_name": name,
                    "quantity": row["stock_quantity"],
                    "distance_km": dist,
                }
            )
        alternatives.sort(key=lambda a: a["quantity"], reverse=True)
        alternatives = alternatives[:3]  # max 3 (SPEC-ARIA-04 §4)

    result = {
        "product_id": product_id,
        "available": available,
        "quantity": quantity,
        # aisle_ref present only when available (SPEC-ARIA-04 §4).
        "aisle_ref": (at_store.get("aisle_ref") if available and at_store else None),
        "discount_active": bool(at_store.get("discount_active")) if at_store else False,
        "discounted_price_aed": at_store.get("discounted_price_aed") if at_store else None,
        "alternative_stores": alternatives,
    }
    logger.info(
        "check_stock",
        tool="check_stock",
        product_id=product_id,
        store_id=store_id,
        available=available,
        alternatives_count=len(alternatives),
        status="success",
    )
    return result


class CheckStockRequest(BaseModel):
    product_id: str
    store_id: str


@router.post("/tools/check-stock")
@limiter.limit("60/minute")
async def check_stock_endpoint(request: Request, req: CheckStockRequest) -> dict:
    return check_stock(req.product_id, req.store_id)
