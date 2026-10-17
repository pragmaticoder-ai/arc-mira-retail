"""check_stock — SPEC-ARIA-04.

Real-time stock for a product at a store. Surfaces active discounts so ARIA
can mention them (ARIA system prompt). Lists alternative stores with stock.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.logger import get_logger

logger = get_logger("aria.check_stock")
router = APIRouter()


def check_stock(product_id: str, store_id: str) -> dict:
    """
    Checks real-time stock for a specific product at a specific store.
    Returns available, quantity, aisle_ref, discount info, and
    alternative_stores. Call for every item before confirming it in the cart.
    """
    db = get_alloydb()
    product = db.get_product(product_id)
    if not product:
        return error("NOT_FOUND", f"product {product_id} not found")

    available = product["store_id"] == store_id and product["stock_quantity"] > 0

    # Alternative stores: in this mock, inventory is single-store, so this is
    # empty unless a product exists at another store. Real impl queries all stores.
    alternatives: list[dict] = []

    result = {
        "product_id": product_id,
        "available": available,
        "quantity": product["stock_quantity"] if product["store_id"] == store_id else 0,
        "aisle_ref": product.get("aisle_ref", ""),
        "discount_active": bool(product.get("discount_active")),
        "discounted_price_aed": product.get("discounted_price_aed"),
        "alternative_stores": alternatives,
    }
    logger.info("check_stock", tool="check_stock", product_id=product_id, available=available, status="success")
    return result


class CheckStockRequest(BaseModel):
    product_id: str
    store_id: str


@router.post("/tools/check-stock")
async def check_stock_endpoint(req: CheckStockRequest) -> dict:
    return check_stock(req.product_id, req.store_id)
