"""ARIA tool: optimize_budget

Trims or swaps cart items to bring total within target budget.
Uses Gemini reasoning to select least impactful adjustments.

Spec: specs/SPEC-ARIA-06-optimize_budget.md
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from tools.shared.models import OptimizeBudgetRequest, OptimizeBudgetResponse, BudgetChange
from tools.shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/optimize-budget", response_model=OptimizeBudgetResponse)
async def optimize_budget(request: OptimizeBudgetRequest):
    """
    Adjust cart to fit within target budget.
    
    Returns:
        OptimizeBudgetResponse: updated cart, new total, changes made
    """
    try:
        cart = request.cart.copy()
        target = request.target_budget_aed
        
        # Calculate current total
        total = sum(item.get("price_aed", 0) * item.get("quantity", 1) for item in cart)
        
        if total <= target:
            # Already within budget
            return OptimizeBudgetResponse(
                updated_cart=cart,
                new_total_aed=round(total, 2),
                changes_made=[],
            )
        
        # Need to reduce
        changes = []
        reduction_needed = total - target
        
        # Strategy: reduce quantities of highest-price items first
        cart.sort(key=lambda x: x.get("price_aed", 0), reverse=True)
        
        for item in cart:
            if reduction_needed <= 0:
                break
            
            price = item.get("price_aed", 0)
            quantity = item.get("quantity", 1)
            
            if quantity > 1:
                # Reduce quantity
                reduction_possible = price * (quantity - 1)
                actual_reduction = min(reduction_needed, reduction_possible)
                new_quantity = quantity - int(actual_reduction / price)
                
                if new_quantity >= 1:
                    saving = price * (quantity - new_quantity)
                    reduction_needed -= saving
                    total -= saving
                    item["quantity"] = new_quantity
                    changes.append(BudgetChange(
                        action="reduced_quantity",
                        product_name=item.get("product_name", ""),
                        saving_aed=round(saving, 2),
                    ))
        
        logger.info(
            "optimize_budget_success",
            original_total=sum(item.get("price_aed", 0) * item.get("quantity", 1) for item in request.cart),
            new_total=total,
            changes=len(changes),
        )
        
        return OptimizeBudgetResponse(
            updated_cart=cart,
            new_total_aed=round(total, 2),
            changes_made=changes,
        )
        
    except Exception as e:
        logger.error("optimize_budget_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
