"""Validate and commit an authoritative basket in one storage transaction."""
from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error, is_error
from tools.shared.pricing import quote_cart, valid_amount
from tools.shared.rate_limit import limiter

router = APIRouter()


def place_order(customer_id: str, store_id: str, cart: list[dict], promotion_id: str | None,
                total_aed: float, idempotency_key: str | None = None,
                dietary_preference: str | None = None) -> dict:
    """Reprice a confirmed basket and atomically reserve stock and write its order.
    A session idempotency key is durable; legacy callers get a 60-second window.
    """
    db = get_alloydb()
    with db.transaction():
        customer = db.get_customer(customer_id)
        if not customer:
            return error("NOT_FOUND", "Customer not found")
        if not valid_amount(total_aed):
            return error("VALIDATION_ERROR", "total_aed must be finite and positive")
        # Validate shape before signing; repeated items are consolidated by quote_cart.
        if not cart or any(not isinstance(i, dict) or not isinstance(i.get("product_id"), str)
                           or type(i.get("quantity")) is not int or i["quantity"] <= 0 for i in cart):
            return error("VALIDATION_ERROR", "Cart requires products with positive integer quantities")
        key = hashlib.sha256(json.dumps({"customer": customer_id, "store": store_id,
              "session": idempotency_key, "items": sorted((i["product_id"], i["quantity"]) for i in cart),
              "promotion": promotion_id, "total": round(total_aed, 2)}, sort_keys=True).encode()).hexdigest()
        existing = db.find_order(key, max_age_seconds=None if idempotency_key else 60)
        if existing:
            return _format(existing)
        quote = quote_cart(cart, store_id, dietary_preference or customer["dietary_preference"],
                           promotion_id=promotion_id, select_promotion=False)
        if is_error(quote):
            return quote
        if abs(round(total_aed, 2) - quote["total_aed"]) > 0.001:
            return error("VALIDATION_ERROR", "Price changed or total is invalid; review an updated quote")
        for item in quote["items"]:
            db.decrement_stock(item["product_id"], store_id, item["quantity"])
        if promotion_id:
            db.increment_promotion_usage(promotion_id)
        order = db.insert_order({"customer_id": customer_id, "store_id": store_id,
                                 "items": quote["items"], "total_aed": quote["total_aed"],
                                 "promotion_id": promotion_id, "idempotency_key": key})
        return _format(order)


def _format(order: dict) -> dict:
    return {k: order[k] for k in ("order_id", "status", "total_aed", "estimated_delivery_window")}


class PlaceOrderRequest(BaseModel):
    customer_id: str
    store_id: str
    cart: list[dict]
    promotion_id: str | None = None
    total_aed: float = Field(gt=0, allow_inf_nan=False)
    idempotency_key: str | None = None


@router.post("/tools/place-order")
@limiter.limit("10/minute")
async def place_order_endpoint(request: Request, req: PlaceOrderRequest) -> dict:
    return place_order(req.customer_id, req.store_id, req.cart, req.promotion_id, req.total_aed, req.idempotency_key)
