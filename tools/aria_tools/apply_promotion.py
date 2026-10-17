"""apply_promotion — SPEC-ARIA-07.

Checks active promotions and applies the highest-value relevant one matching
dietary preference and min-cart threshold. Returns null application if none fit.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.logger import get_logger

logger = get_logger("aria.apply_promotion")
router = APIRouter()


def _cart_total(cart: list[dict]) -> float:
    return round(sum(i["price_aed"] * i["quantity"] for i in cart), 2)


def _discount_for(promo: dict, cart_total_aed: float) -> float:
    if promo.get("discount_pct"):
        return round(cart_total_aed * float(promo["discount_pct"]) / 100.0, 2)
    if promo.get("discount_flat_aed"):
        return round(float(promo["discount_flat_aed"]), 2)
    return 0.0


def apply_promotion(
    cart: list[dict],
    cart_total_aed: float,
    dietary_preference: str,
    store_id: str,
) -> dict:
    """
    Checks the promotions table for applicable active promotions. Applies the
    highest-value relevant promotion matching dietary_preference. Returns
    promotion details and new_total_aed. Call after optimize_budget().
    """
    if not isinstance(cart, list):
        return error("VALIDATION_ERROR", "cart must be a list")

    db = get_alloydb()
    promos = db.list_active_promotions(store_id)

    cats_in_cart = set()
    for i in cart:
        p = db.get_product(i["product_id"])
        if p:
            cats_in_cart.add(p["category"])

    best = None
    best_discount = 0.0
    for promo in promos:
        if cart_total_aed < float(promo.get("min_cart_aed", 0)):
            continue
        df = promo.get("dietary_filter")
        if df and df != dietary_preference:
            continue
        cat = promo.get("category")
        if cat and cat != "all" and cat not in cats_in_cart:
            continue
        discount = _discount_for(promo, cart_total_aed)
        if discount > best_discount:
            best, best_discount = promo, discount

    if not best:
        return {
            "promotion_applied": False,
            "promotion_id": None,
            "promotion_name": None,
            "discount_aed": 0.0,
            "new_total_aed": round(cart_total_aed, 2),
            "reason": "No applicable promotion for this cart",
        }

    new_total = round(cart_total_aed - best_discount, 2)
    result = {
        "promotion_applied": True,
        "promotion_id": best["promotion_id"],
        "promotion_name": best["name"],
        "discount_aed": best_discount,
        "new_total_aed": new_total,
        "reason": best.get("description", best["name"]),
    }
    logger.info(
        "apply_promotion",
        tool="apply_promotion",
        promotion_id=best["promotion_id"],
        discount_aed=best_discount,
        status="success",
    )
    return result


class ApplyPromotionRequest(BaseModel):
    cart: list[dict]
    cart_total_aed: float
    dietary_preference: str
    store_id: str


@router.post("/tools/apply-promotion")
async def apply_promotion_endpoint(req: ApplyPromotionRequest) -> dict:
    return apply_promotion(req.cart, req.cart_total_aed, req.dietary_preference, req.store_id)
