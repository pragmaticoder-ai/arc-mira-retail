"""ARIA tool: check_stock

Checks real-time stock for a specific product at a specific store.

Spec: specs/SPEC-ARIA-04-check_stock.md
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from tools.shared.models import CheckStockRequest, CheckStockResponse, AlternativeStore
from tools.shared.alloydb_client import get_alloydb
from tools.shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/check-stock", response_model=CheckStockResponse)
async def check_stock(request: CheckStockRequest):
    """
    Check real-time stock for a product at a store.
    
    Returns:
        CheckStockResponse: availability, quantity, aisle, alternatives
    """
    try:
        db = get_alloydb()
        
        # Get product
        product = db.get_product(request.product_id)
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {request.product_id} not found"
            )
        
        # Check stock at requested store
        in_stock = product.get("store_id") == request.store_id and product.get("stock_quantity", 0) > 0
        quantity = product.get("stock_quantity", 0) if in_stock else 0
        
        # Find alternative stores (mock: return empty list)
        alternatives = []
        if not in_stock:
            # In real implementation, query inventory for other stores
            pass
        
        logger.info(
            "check_stock_success",
            product_id=request.product_id,
            store_id=request.store_id,
            available=in_stock,
            quantity=quantity,
        )
        
        return CheckStockResponse(
            product_id=request.product_id,
            available=in_stock,
            quantity=quantity,
            aisle_ref=product.get("aisle_ref", ""),
            alternative_stores=alternatives,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("check_stock_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
