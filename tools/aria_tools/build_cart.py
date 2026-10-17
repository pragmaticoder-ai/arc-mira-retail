"""build_cart — SPEC-ARIA-03.

Builds a grocery cart from inventory matching the customer goal, dietary
preference, and budget. Restricted to the 8 allowed grocery categories.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.llm import ALLOWED_CATEGORIES, get_llm
from tools.shared.logger import get_logger

logger = get_logger("aria.build_cart")
router = APIRouter()

_VALID_DIET = {"halal", "vegetarian", "vegan", "none"}


def _household_multiplier(household_size: int) -> int:
    if household_size <= 2:
        return 1
    if household_size <= 4:
        return 2
    return 3


def build_cart(
    goal: str,
    dietary_preference: str,
    budget_aed: float,
    household_size: int,
    store_id: str,
) -> dict:
    """
    Builds a grocery cart from AlloyDB inventory matching the customer goal.
    Restricted to grocery categories only. Filters by dietary_preference and
    selects best-value items within budget_aed. Returns items, total_aed, and
    items_unavailable. Call after get_customer_context().
    """
    # ── Validation (SPEC-ARIA-03 §4) ─────────────────────────────────
    if not goal or not goal.strip():
        return error("VALIDATION_ERROR", "goal is empty")
    if len(goal) > 500:
        return error("VALIDATION_ERROR", "goal exceeds 500 chars")
    if dietary_preference not in _VALID_DIET:
        return error("VALIDATION_ERROR", f"invalid dietary_preference: {dietary_preference}")
    if budget_aed is None or budget_aed <= 0 or budget_aed > 10000:
        return error("VALIDATION_ERROR", "budget_aed must be in (0, 10000]")
    if not (1 <= household_size <= 20):
        return error("VALIDATION_ERROR", "household_size must be 1..20")

    db = get_alloydb()
    inv = db.list_inventory(store_id)
    if not inv:
        return error("NOT_FOUND", f"store {store_id} has no inventory")

    # ── Map goal -> allowed categories ───────────────────────────────
    categories = get_llm().classify_goal_to_categories(goal)
    categories = [c for c in categories if c in ALLOWED_CATEGORIES] or ALLOWED_CATEGORIES

    mult = _household_multiplier(household_size)
    items: list[dict] = []
    unavailable: list[dict] = []
    total = 0.0

    # One representative item per category: cheapest in-stock dietary match.
    for cat in categories:
        cat_products = [p for p in inv if p["category"] == cat]
        if dietary_preference != "none":
            cat_products = [p for p in cat_products if dietary_preference in p["dietary_flags"]]
        if not cat_products:
            continue
        cat_products.sort(key=lambda p: p["price_aed"])
        in_stock = [p for p in cat_products if p["stock_quantity"] > 0]
        oos = [p for p in cat_products if p["stock_quantity"] <= 0]

        if in_stock:
            p = in_stock[0]
            price = (
                p["discounted_price_aed"]
                if p.get("discount_active") and p.get("discounted_price_aed")
                else p["price_aed"]
            )
            # Stay within budget as we add items.
            if total + price * mult > budget_aed and items:
                continue
            items.append(
                {
                    "product_id": p["product_id"],
                    "product_name": p["product_name"],
                    "quantity": mult,
                    "price_aed": float(price),
                    "aisle_ref": p["aisle_ref"],
                    "in_stock": True,
                    "substituted": False,
                    "discount_active": bool(p.get("discount_active")),
                }
            )
            total += price * mult
        elif oos:
            p = oos[0]
            unavailable.append({"product_id": p["product_id"], "product_name": p["product_name"]})

    result = {
        "items": items,
        "total_aed": round(total, 2),
        "items_unavailable": unavailable,
    }
    logger.info(
        "build_cart",
        tool="build_cart",
        store_id=store_id,
        dietary_preference=dietary_preference,
        items_returned=len(items),
        total_aed=result["total_aed"],
        status="success",
    )
    return result


class BuildCartRequest(BaseModel):
    goal: str
    dietary_preference: str
    budget_aed: float
    household_size: int
    store_id: str


@router.post("/tools/build-cart")
async def build_cart_endpoint(req: BuildCartRequest) -> dict:
    return build_cart(
        req.goal, req.dietary_preference, req.budget_aed, req.household_size, req.store_id
    )
