"""optimize_budget — SPEC-ARIA-06.

Trims/swaps cart items to bring total within target_budget_aed. Mock uses a
greedy "drop the most expensive non-essential items" heuristic (real impl uses
Gemini reasoning). Always reports what changed and why.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.errors import error
from tools.shared.logger import get_logger

logger = get_logger("aria.optimize_budget")
router = APIRouter()


def _cart_total(cart: list[dict]) -> float:
    return round(sum(i["price_aed"] * i["quantity"] for i in cart), 2)


_VALID_DIET = {"halal", "vegetarian", "vegan", "none"}
_FLOOR_PCT = 0.85  # SPEC-ARIA-06: don't trim below 85% of target


def optimize_budget(cart: list[dict], target_budget_aed: float, dietary_preference: str = "none") -> dict:
    """
    Trims or swaps cart items to bring total within target_budget_aed.
    Returns updated_cart, new_total_aed, and changes_made. Call when cart
    total exceeds customer budget. Always explain changes.
    """
    # ── Validation (SPEC-ARIA-06 §4) ─────────────────────────────────
    if not isinstance(cart, list) or len(cart) < 1:
        return error("VALIDATION_ERROR", "cart must have at least 1 item")
    if target_budget_aed is None or target_budget_aed <= 0:
        return error("VALIDATION_ERROR", "target_budget_aed must be > 0")
    if dietary_preference not in _VALID_DIET:
        return error("VALIDATION_ERROR", f"invalid dietary_preference: {dietary_preference}")
    for i in cart:
        if not i.get("product_id") or i.get("quantity", 0) < 1 or i.get("price_aed", 0) <= 0:
            return error("VALIDATION_ERROR", "every cart item needs product_id, quantity>=1, price_aed>0")

    updated = [dict(i) for i in cart]
    changes: list[dict] = []
    total = _cart_total(updated)

    # Already within budget → no changes.
    if total <= target_budget_aed:
        return {"updated_cart": updated, "new_total_aed": total, "changes_made": []}

    floor = target_budget_aed * _FLOOR_PCT

    # Greedy: reduce quantity of the most expensive line, dropping it if it
    # hits zero. Stop once within budget, keeping >= 1 item.
    guard = 0
    while total > target_budget_aed and len(updated) > 1 and guard < 500:
        guard += 1
        updated.sort(key=lambda i: i["price_aed"] * i["quantity"], reverse=True)
        top = updated[0]
        if top["quantity"] > 1:
            top["quantity"] -= 1
            changes.append({"action": "reduced_quantity", "product_name": top["product_name"], "saving_aed": round(top["price_aed"], 2)})
        else:
            updated.pop(0)
            changes.append({"action": "removed", "product_name": top["product_name"], "saving_aed": round(top["price_aed"], 2)})
        total = _cart_total(updated)

    # Can't get within budget at all (one expensive essential left).
    if total > target_budget_aed:
        return error("UNPROCESSABLE", "cannot reach target budget without removing essential items")

    # Over-trimmed below the floor — the cart can't be optimised to land in the
    # [floor, target] band without cutting essentials. Signal rather than
    # return a cart that's been gutted (SPEC-ARIA-06 §4).
    if total < floor:
        return error("UNPROCESSABLE", "cannot reach target budget without over-trimming the cart")

    result = {"updated_cart": updated, "new_total_aed": total, "changes_made": changes}
    logger.info("optimize_budget", tool="optimize_budget", original_total=_cart_total(cart),
                target_budget=target_budget_aed, new_total=total, changes_count=len(changes), status="success")
    return result


class OptimizeBudgetRequest(BaseModel):
    cart: list[dict]
    target_budget_aed: float
    dietary_preference: str = "none"


@router.post("/tools/optimize-budget")
async def optimize_budget_endpoint(req: OptimizeBudgetRequest) -> dict:
    return optimize_budget(req.cart, req.target_budget_aed, req.dietary_preference)
