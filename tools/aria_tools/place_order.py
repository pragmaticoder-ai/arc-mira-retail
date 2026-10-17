"""place_order — SPEC-ARIA-08.

Writes the confirmed order to AlloyDB (mock adapter). Only called after
explicit customer confirmation (the agent enforces the confirmation phrase).
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.logger import get_logger

logger = get_logger("aria.place_order")
router = APIRouter()


def place_order(
    customer_id: str,
    store_id: str,
    cart: list[dict],
    promotion_id: str | None,
    total_aed: float,
) -> dict:
    """
    Writes the confirmed order to the AlloyDB orders table. Returns order_id,
    status, total_aed, estimated_delivery_window. Only call after receiving
    explicit customer confirmation.
    """
    if not cart:
        return error("VALIDATION_ERROR", "cart is empty")
    if total_aed is None or total_aed <= 0:
        return error("VALIDATION_ERROR", "total_aed must be > 0")

    db = get_alloydb()
    if not db.get_customer(customer_id):
        return error("NOT_FOUND", f"customer {customer_id} not found")

    order = db.insert_order(
        {
            "customer_id": customer_id,
            "store_id": store_id,
            "items": cart,
            "total_aed": round(total_aed, 2),
            "promotion_id": promotion_id,
        }
    )
    result = {
        "order_id": order["order_id"],
        "status": order["status"],
        "total_aed": round(total_aed, 2),
        "estimated_delivery_window": order["estimated_delivery_window"],
    }
    logger.info("place_order", tool="place_order", order_id=order["order_id"], status="success")
    return result


class PlaceOrderRequest(BaseModel):
    customer_id: str
    store_id: str
    cart: list[dict]
    promotion_id: str | None = None
    total_aed: float


@router.post("/tools/place-order")
async def place_order_endpoint(req: PlaceOrderRequest) -> dict:
    return place_order(req.customer_id, req.store_id, req.cart, req.promotion_id, req.total_aed)
