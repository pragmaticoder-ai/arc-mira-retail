"""place_order — SPEC-ARIA-08.

Writes the confirmed order to AlloyDB (mock adapter). Only called after
explicit customer confirmation (the agent enforces the confirmation phrase).
"""

from __future__ import annotations

import hashlib
import json
import time

from fastapi import APIRouter, Request
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.logger import get_logger
from tools.shared.rate_limit import limiter

logger = get_logger("aria.place_order")
router = APIRouter()

# 60-second idempotency window (SPEC-ARIA-08 §9): signature -> (ts, order).
_IDEMPOTENCY_WINDOW_S = 60
_recent: dict[str, tuple[float, dict]] = {}


def _order_signature(customer_id: str, store_id: str, cart: list[dict], total_aed: float) -> str:
    payload = json.dumps(
        {"c": customer_id, "s": store_id,
         "items": sorted((i["product_id"], i["quantity"]) for i in cart),
         "t": round(total_aed, 2)},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _recent_order(signature: str) -> dict | None:
    entry = _recent.get(signature)
    if not entry:
        return None
    ts, order = entry
    if time.time() - ts > _IDEMPOTENCY_WINDOW_S:
        _recent.pop(signature, None)
        return None
    return order


def _remember_order(signature: str, order: dict) -> None:
    _recent[signature] = (time.time(), order)


def _format(order: dict, total_aed: float) -> dict:
    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "total_aed": round(total_aed, 2),
        "estimated_delivery_window": order["estimated_delivery_window"],
    }


def place_order(
    customer_id: str,
    store_id: str,
    cart: list[dict],
    promotion_id: str | None,
    total_aed: float,
) -> dict:
    """
    Writes the confirmed order to the AlloyDB orders table, re-verifying and
    decrementing stock atomically. Returns order_id, status, total_aed,
    estimated_delivery_window. Only call after explicit customer confirmation.
    """
    # ── Validation (SPEC-ARIA-08 §4) ─────────────────────────────────
    if not cart:
        return error("VALIDATION_ERROR", "cart is empty")
    if total_aed is None or total_aed <= 0:
        return error("VALIDATION_ERROR", "total_aed must be > 0")

    db = get_alloydb()
    if not db.get_customer(customer_id):
        return error("NOT_FOUND", f"customer {customer_id} not found")
    if promotion_id and not any(p["promotion_id"] == promotion_id for p in db.list_active_promotions(store_id)):
        return error("NOT_FOUND", f"promotion {promotion_id} not found")

    # total_aed must match the cart sum within AED 0.01 — unless a promotion
    # discount is applied (then total is below the raw sum, which is expected).
    cart_sum = round(sum(i["price_aed"] * i["quantity"] for i in cart), 2)
    if promotion_id is None and abs(cart_sum - round(total_aed, 2)) > 0.01:
        return error("VALIDATION_ERROR", f"total_aed {total_aed} does not match cart sum {cart_sum}")
    if promotion_id is not None and round(total_aed, 2) > cart_sum + 0.01:
        return error("VALIDATION_ERROR", "total_aed exceeds cart sum")

    # Idempotency: same customer + same cart within 60s returns the prior order.
    signature = _order_signature(customer_id, store_id, cart, total_aed)
    existing = _recent_order(signature)
    if existing:
        logger.info("place_order", tool="place_order", order_id=existing["order_id"],
                    idempotent=True, status="success")
        return _format(existing, total_aed)

    # Re-verify stock at order time for every item (SPEC-ARIA-08 §3).
    for item in cart:
        row = db.get_product_at_store(item["product_id"], store_id)
        have = row["stock_quantity"] if row else 0
        if have < item["quantity"]:
            return error("VALIDATION_ERROR", f"insufficient stock for {item['product_id']} (have {have}, need {item['quantity']})")

    # Atomic-ish: in the mock, decrement after the full check passed so a
    # mid-loop failure can't partially decrement. Real impl wraps a DB txn.
    for item in cart:
        db.decrement_stock(item["product_id"], store_id, item["quantity"])

    order = db.insert_order(
        {
            "customer_id": customer_id,
            "store_id": store_id,
            "items": cart,
            "total_aed": round(total_aed, 2),
            "promotion_id": promotion_id,
        }
    )
    _remember_order(signature, order)
    logger.info("place_order", tool="place_order", order_id=order["order_id"],
                customer_id=customer_id, total_aed=round(total_aed, 2),
                items_count=len(cart), status="success")
    return _format(order, total_aed)


class PlaceOrderRequest(BaseModel):
    customer_id: str
    store_id: str
    cart: list[dict]
    promotion_id: str | None = None
    total_aed: float


@router.post("/tools/place-order")
@limiter.limit("10/minute")
async def place_order_endpoint(request: Request, req: PlaceOrderRequest) -> dict:
    return place_order(req.customer_id, req.store_id, req.cart, req.promotion_id, req.total_aed)
