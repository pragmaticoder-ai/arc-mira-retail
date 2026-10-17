"""ARIA tool: build_cart

Builds a grocery cart from AlloyDB inventory matching customer goal,
dietary preference, and budget.

Spec: specs/SPEC-ARIA-03-build_cart.md
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from tools.shared.models import (
    BuildCartRequest,
    BuildCartResponse,
    CartItem,
    UnavailableItem,
)
from tools.shared.alloydb_client import get_alloydb
from tools.shared.logger import get_logger
from tools.shared.settings import settings

router = APIRouter()
logger = get_logger(__name__)

ALLOWED_CATEGORIES = [
    "dairy", "grains", "halal_meat", "vegetables",
    "fruits", "beverages", "snacks", "condiments",
]


async def map_goal_to_categories(goal: str) -> list[str]:
    """
    Map customer goal to grocery categories.
    
    Uses Gemini Flash in production, keyword matching in mock mode.
    """
    if settings.use_mock:
        goal_lower = goal.lower()
        
        if "biryani" in goal_lower:
            return ["grains", "halal_meat", "condiments", "vegetables"]
        elif "breakfast" in goal_lower:
            return ["dairy", "grains", "fruits", "beverages"]
        elif "weekly" in goal_lower or "groceries" in goal_lower:
            return ["dairy", "grains", "halal_meat", "vegetables", "fruits", "beverages"]
        else:
            return ["dairy", "grains", "halal_meat", "vegetables", "fruits"]
    
    # Production: call Gemini to map goal to categories
    # TODO: Implement real Gemini API call
    return ["dairy", "grains", "halal_meat", "vegetables", "fruits", "beverages"]


def calculate_quantity_multiplier(household_size: int) -> int:
    """Calculate quantity multiplier based on household size."""
    if household_size <= 2:
        return 1
    elif household_size <= 4:
        return 2
    else:
        return 3


@router.post("/build-cart", response_model=BuildCartResponse)
async def build_cart(request: BuildCartRequest):
    """
    Build a grocery cart matching customer goal, dietary, and budget.
    
    Returns:
        BuildCartResponse: items list, total, unavailable items
        
    Raises:
        HTTPException: 400 if validation fails, 404 if store not found
    """
    try:
        db = get_alloydb()
        
        # Step 1: Map goal to categories
        categories = await map_goal_to_categories(request.goal)
        
        # Filter to only allowed categories
        categories = [c for c in categories if c in ALLOWED_CATEGORIES]
        
        if not categories:
            raise HTTPException(
                status_code=400,
                detail="No valid grocery categories found in goal"
            )
        
        # Step 2: Query inventory for each category
        all_products = []
        for category in categories:
            products = db.list_inventory(request.store_id, category=category)
            all_products.extend(products)
        
        # Step 3: Filter by dietary preference
        if request.dietary_preference != "none":
            filtered = []
            for p in all_products:
                dietary_flags = p.get("dietary_flags", "")
                if request.dietary_preference in dietary_flags:
                    filtered.append(p)
            all_products = filtered
        
        # Step 4: Select items based on household size and budget
        quantity_mult = calculate_quantity_multiplier(request.household_size)
        
        items = []
        unavailable = []
        total = 0.0
        
        # Sort by price to fit budget
        all_products.sort(key=lambda p: p.get("price_aed", 0))
        
        # Select representative items per category
        seen_categories = set()
        for product in all_products:
            if total >= request.budget_aed:
                break
            
            category = product.get("category")
            if category in seen_categories and len(seen_categories) >= 6:
                continue
            
            # Calculate quantity
            quantity = quantity_mult
            price = product.get("price_aed", 0) * quantity
            
            # Check if within budget
            if total + price > request.budget_aed:
                # Reduce quantity or skip
                quantity = max(1, int((request.budget_aed - total) / product.get("price_aed", 1)))
                if quantity == 0:
                    continue
                price = product.get("price_aed", 0) * quantity
            
            # Check stock
            in_stock = product.get("stock_quantity", 0) > 0
            
            if in_stock:
                items.append(CartItem(
                    product_id=product["product_id"],
                    product_name=product["product_name"],
                    quantity=quantity,
                    price_aed=product.get("price_aed", 0),
                    aisle_ref=product.get("aisle_ref", ""),
                    in_stock=True,
                ))
                total += price
                seen_categories.add(category)
            else:
                unavailable.append(UnavailableItem(
                    product_id=product["product_id"],
                    product_name=product["product_name"],
                ))
        
        logger.info(
            "build_cart_success",
            store_id=request.store_id,
            items=len(items),
            unavailable=len(unavailable),
            total_aed=total,
        )
        
        return BuildCartResponse(
            items=items,
            total_aed=round(total, 2),
            items_unavailable=unavailable,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("build_cart_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
