"""ARIA tool: get_customer_context

Retrieves customer profile and last 3 orders from AlloyDB.

Spec: specs/SPEC-ARIA-02-get_customer_context.md
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from tools.shared.models import (
    GetCustomerContextRequest,
    GetCustomerContextResponse,
    LastOrder,
)
from tools.shared.alloydb_client import get_alloydb
from tools.shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/get-customer-context", response_model=GetCustomerContextResponse)
async def get_customer_context(request: GetCustomerContextRequest):
    """
    Retrieve customer profile and recent orders from AlloyDB.
    
    This MUST be called before building any cart.
    
    Returns:
        GetCustomerContextResponse: customer profile with last orders
        
    Raises:
        HTTPException: 404 if customer not found
    """
    try:
        db = get_alloydb()
        
        # Get customer profile
        customer = db.get_customer(request.customer_id)
        
        if not customer:
            logger.error("customer_not_found", customer_id=request.customer_id)
            raise HTTPException(
                status_code=404,
                detail=f"Customer {request.customer_id} not found"
            )
        
        # Get last orders (mock: return empty list for now)
        # In real implementation, query orders table
        last_orders = []
        
        logger.info(
            "get_customer_context_success",
            customer_id=request.customer_id,
            dietary=customer.get("dietary_preference"),
        )
        
        return GetCustomerContextResponse(
            customer_id=customer["customer_id"],
            name=customer["name"],
            dietary_preference=customer.get("dietary_preference", "none"),
            household_size=customer.get("household_size", 1),
            weekly_budget_aed=customer.get("weekly_budget_aed", 0.0),
            preferred_store=customer.get("preferred_store", ""),
            last_orders=last_orders,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_customer_context_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
