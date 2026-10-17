"""ARIA tool: apply_promotion

Checks for applicable promotions and applies the best one to the cart.

Spec: specs/SPEC-ARIA-07-apply_promotion.md
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from tools.shared.models import ApplyPromotionRequest, ApplyPromotionResponse
from tools.shared.alloydb_client import get_alloydb
from tools.shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/apply-promotion", response_model=ApplyPromotionResponse)
async def apply_promotion(request: ApplyPromotionRequest):
    """
    Find and apply the best promotion for the cart.
    
    Returns:
        ApplyPromotionResponse: promotion details and new total
    """
    try:
        db = get_alloydb()
        
        # Get active promotions
        promotions = db.list_active_promotions(request.store_id)
        
        best_promotion = None
        best_discount = 0.0
        
        # Find best applicable promotion
        for promo in promotions:
            # Check minimum cart value
            min_cart = promo.get("min_cart_aed", 0)
            if request.cart_total_aed < min_cart:
                continue
            
            # Check dietary filter
            dietary_filter = promo.get("dietary_filter")
            if dietary_filter and dietary_filter != request.dietary_preference:
                continue
            
            # Calculate discount
            discount_pct = promo.get("discount_pct", 0)
            discount = request.cart_total_aed * (discount_pct / 100)
            
            if discount > best_discount:
                best_discount = discount
                best_promotion = promo
        
        if not best_promotion:
            return ApplyPromotionResponse(
                promotion_applied=False,
                new_total_aed=request.cart_total_aed,
                reason="No applicable promotions found",
            )
        
        new_total = request.cart_total_aed - best_discount
        
        logger.info(
            "apply_promotion_success",
            promotion_id=best_promotion["promotion_id"],
            discount_aed=best_discount,
            new_total_aed=new_total,
        )
        
        return ApplyPromotionResponse(
            promotion_applied=True,
            promotion_id=best_promotion["promotion_id"],
            promotion_name=best_promotion["name"],
            discount_aed=round(best_discount, 2),
            new_total_aed=round(new_total, 2),
            reason=f"Applied {best_promotion['name']} ({best_promotion.get('discount_pct', 0)}% off)",
        )
        
    except Exception as e:
        logger.error("apply_promotion_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
