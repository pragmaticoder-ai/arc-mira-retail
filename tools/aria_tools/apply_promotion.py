"""apply_promotion — SPEC-ARIA-07.

Checks active promotions and applies the highest-value relevant one matching
dietary preference and min-cart threshold. Returns null application if none fit.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Request
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.clock import today
from tools.shared.errors import error
from tools.shared.logger import get_logger
from tools.shared.rate_limit import limiter

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


_VALID_DIET = {"halal", "vegetarian", "vegan", "none"}
# Session-scoped idempotency: promotions already applied this session.
_applied_this_session: set[tuple[str, str]] = set()


def _is_valid_now(promo: dict) -> bool:
    if not promo.get("is_active"):
        return False
    vf, vu = promo.get("valid_from"), promo.get("valid_until")
    try:
        if vf and date.fromisoformat(vf) > today():
            return False
        if vu and date.fromisoformat(vu) < today():
            return False
    except ValueError:
        return False
    max_uses = promo.get("max_uses")
    if max_uses is not None and int(promo.get("times_applied", 0)) >= int(max_uses):
        return False
    return True


def apply_promotion(
    cart: list[dict],
    cart_total_aed: float,
    dietary_preference: str,
    store_id: str,
    session_id: str | None = None,
    *, promotion_id: str | None = None, record_usage: bool = False,
) -> dict:
    """
    Checks the promotions table for applicable active promotions. Applies the
    highest-value relevant promotion matching dietary_preference. Returns
    promotion details and new_total_aed. Call after optimize_budget().
    """
    # ── Validation (SPEC-ARIA-07 §4) ─────────────────────────────────
    if not isinstance(cart, list) or len(cart) < 1:
        return error("VALIDATION_ERROR", "cart must have at least 1 item")
    if cart_total_aed is None or cart_total_aed <= 0:
        return error("VALIDATION_ERROR", "cart_total_aed must be > 0")
    if dietary_preference not in _VALID_DIET:
        return error("VALIDATION_ERROR", f"invalid dietary_preference: {dietary_preference}")

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
        if promotion_id and promo["promotion_id"] != promotion_id:
            continue
        if not _is_valid_now(promo):  # expiry + max_uses + active
            continue
        if cart_total_aed < float(promo.get("min_cart_aed", 0)):
            continue
        df = promo.get("dietary_filter")
        if df and df != dietary_preference:
            continue
        cat = promo.get("category")
        if cat and cat != "all" and cat not in cats_in_cart:
            continue
        eligible_total = sum(i["price_aed"] * i["quantity"] for i in cart
                             if not cat or cat == "all" or
                             (db.get_product_at_store(i["product_id"], store_id) or {}).get("category") == cat)
        discount = _discount_for(promo, eligible_total)
        if discount > best_discount:
            best, best_discount = promo, discount

    if not best:
        return {
            "promotion_applied": False,
            "promotion_id": None,
            "promotion_name": None,
            "discount_aed": 0.0,
            "new_total_aed": round(cart_total_aed, 2),
            "reason": "No applicable promotions for this cart",
        }

    new_total = round(cart_total_aed - best_discount, 2)
    # A promotion can never make the cart free/negative (SPEC-ARIA-07 §6).
    if new_total <= 0:
        return error("UNPROCESSABLE", "promotion would reduce the cart to zero or below")

    # Idempotency: applying the same promotion twice in a session is a no-op
    # on the usage counter (SPEC-ARIA-07 §9).
    key = (session_id or "", best["promotion_id"])
    if record_usage and (session_id is None or key not in _applied_this_session):
        db.increment_promotion_usage(best["promotion_id"])
        if session_id is not None:
            _applied_this_session.add(key)

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
        cart_total_before=round(cart_total_aed, 2),
        status="success",
    )
    return result


class ApplyPromotionRequest(BaseModel):
    cart: list[dict]
    cart_total_aed: float
    dietary_preference: str
    store_id: str
    session_id: str | None = None


@router.post("/tools/apply-promotion")
@limiter.limit("60/minute")
async def apply_promotion_endpoint(request: Request, req: ApplyPromotionRequest) -> dict:
    return apply_promotion(
        req.cart, req.cart_total_aed, req.dietary_preference, req.store_id, req.session_id
    )
