"""ARIA tool: suggest_substitution

Uses AlloyDB AI vector search to find semantically similar in-stock products.

Spec: specs/SPEC-ARIA-05-suggest_substitution.md
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from tools.shared.models import SuggestSubstitutionRequest, SuggestSubstitutionResponse
from tools.shared.alloydb_client import get_alloydb
from tools.shared.logger import get_logger
from tools.shared.settings import settings

router = APIRouter()
logger = get_logger(__name__)


@router.post("/suggest-substitution", response_model=SuggestSubstitutionResponse)
async def suggest_substitution(request: SuggestSubstitutionRequest):
    """
    Find a substitute product using semantic similarity search.
    
    Returns:
        SuggestSubstitutionResponse: substitute product details
    """
    try:
        db = get_alloydb()
        
        # Get original product
        original = db.get_product(request.product_id)
        if not original:
            raise HTTPException(
                status_code=404,
                detail=f"Product {request.product_id} not found"
            )
        
        # Find substitutes
        # In production: use AlloyDB AI vector search (ScaNN)
        # In mock mode: keyword matching on category and price
        
        if settings.use_mock:
            # Mock: find products in same category within price range
            inventory = db.list_inventory(request.store_id)
            
            candidates = []
            for product in inventory:
                # Skip original product
                if product["product_id"] == request.product_id:
                    continue
                
                # Check stock
                if product.get("stock_quantity", 0) <= 0:
                    continue
                
                # Check dietary
                dietary_flags = product.get("dietary_flags", "")
                if request.dietary_preference != "none" and request.dietary_preference not in dietary_flags:
                    continue
                
                # Check price (within 20% of max)
                price = product.get("price_aed", 0)
                if price > request.max_price_aed:
                    continue
                
                # Check same category
                if product.get("category") == original.get("category"):
                    # Calculate similarity (mock: based on price proximity)
                    similarity = 1.0 - abs(price - original.get("price_aed", 0)) / max(price, original.get("price_aed", 1))
                    candidates.append((product, similarity))
            
            # Sort by similarity
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            if not candidates:
                raise HTTPException(
                    status_code=404,
                    detail="No suitable substitute found"
                )
            
            best_match, similarity = candidates[0]
            
            return SuggestSubstitutionResponse(
                substitute_product_id=best_match["product_id"],
                name=best_match["product_name"],
                price_aed=best_match.get("price_aed", 0),
                similarity_score=round(similarity, 2),
                reason=f"Same category ({best_match.get('category')}), in stock, within budget",
                in_stock=True,
            )
        
        # Production: use vector search
        # TODO: Implement real AlloyDB AI vector search
        raise NotImplementedError("Vector search not implemented in production yet")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("suggest_substitution_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
