"""ARIA tool: place_order

Writes the confirmed order to AlloyDB orders table.

Spec: specs/SPEC-ARIA-08-place_order.md
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from tools.shared.models import PlaceOrderRequest, PlaceOrderResponse
from tools.shared.alloydb_client import get_alloydb
from tools.shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

CONFIRMATION_PHRASES = ["confirm", "yes", "place order", "go ahead", "proceed"]


@router.post("/place-order", response_model=PlaceOrderResponse)
async def place_order(request: PlaceOrderRequest):
    """
    Place the confirmed order.
    
    IMPORTANT: Only call after explicit customer confirmation.
    
    Returns:
        PlaceOrderResponse: order_id, status, total, delivery window
    """
    try:
        db = get_alloydb()
        
        # Create order record
        order_data = {
            "customer_id": request.customer_id,
            "store_id": request.store_id,
            "items": request.cart,
            "total_aed": request.total_aed,
            "promotion_id": request.promotion_id,
        }
        
        order = db.insert_order(order_data)
        
        logger.info(
            "place_order_success",
            order_id=order["order_id"],
            customer_id=request.customer_id,
            total_aed=request.total_aed,
        )
        
        return PlaceOrderResponse(
            order_id=order["order_id"],
            status=order["status"],
            total_aed=order.get("total_aed", request.total_aed),
            estimated_delivery_window=order.get("estimated_delivery_window", ""),
        )
        
    except Exception as e:
        logger.error("place_order_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
