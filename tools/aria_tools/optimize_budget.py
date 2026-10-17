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


def optimize_budget(cart: list[dict], target_budget_aed: float, dietary_preference: str = "none") -> dict:
    """
    Trims or swaps cart items to bring total within target_budget_aed.
    Returns updated_cart, new_total_aed, and changes_made. Call when cart
    total exceeds customer budget. Always explain changes.
    """
    if target_budget_aed is None or target_budget_aed <= 0:
        return error("VALIDATION_ERROR", "target_budget_aed must be > 0")
    if not isinstance(cart, list):
        return error("VALIDATION_ERROR", "cart must be a list")

    updated = [dict(i) for i in cart]
    changes: list[dict] = []
    total = _cart_total(updated)

    # Greedy: while over budget, reduce quantity of the most expensive line,
    # dropping it entirely if quantity hits zero. Keep at least one item.
    guard = 0
    while total > target_budget_aed and len(updated) > 1 and guard < 100:
        guard += 1
        updated.sort(key=lambda i: i["price_aed"] * i["quantity"], reverse=True)
        top = updated[0]
        if top["quantity"] > 1:
            top["quantity"] -= 1
            changes.append(
                {"action": "reduced_quantity", "product_name": top["product_name"], "saving_aed": round(top["price_aed"], 2)}
            )
        else:
            updated.pop(0)
            changes.append(
                {"action": "removed", "product_name": top["product_name"], "saving_aed": round(top["price_aed"], 2)}
            )
        total = _cart_total(updated)

    result = {
        "updated_cart": updated,
        "new_total_aed": total,
        "changes_made": changes,
    }
    logger.info(
        "optimize_budget",
        tool="optimize_budget",
        new_total_aed=total,
        changes=len(changes),
        status="success",
    )
    return result


class OptimizeBudgetRequest(BaseModel):
    cart: list[dict]
    target_budget_aed: float
    dietary_preference: str = "none"


@router.post("/tools/optimize-budget")
async def optimize_budget_endpoint(req: OptimizeBudgetRequest) -> dict:
    return optimize_budget(req.cart, req.target_budget_aed, req.dietary_preference)
