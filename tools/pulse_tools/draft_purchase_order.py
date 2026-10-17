"""PULSE tool: draft_purchase_order

Creates a pending purchase order for manager approval.

Spec: specs/SPEC-PULSE-05-draft_purchase_order.md
"""

from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, HTTPException
from tools.shared.models import (
    DraftPurchaseOrderRequest,
    DraftPurchaseOrderResponse,
)
from tools.shared.alloydb_client import get_alloydb
from tools.shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/draft-purchase-order", response_model=DraftPurchaseOrderResponse)
async def draft_purchase_order(request: DraftPurchaseOrderRequest):
    """
    Create a pending purchase order.
    
    IMPORTANT: Human approval is ALWAYS required. The system never auto-approves.
    
    Returns:
        DraftPurchaseOrderResponse: PO details with human_approval_required=True
    """
    try:
        db = get_alloydb()
        
        # Get product details
        product = db.get_product(request.product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {request.product_id} not found"
            )
        
        # Create PO record
        po_data = {
            "product_id": request.product_id,
            "store_id": request.store_id,
            "quantity": request.quantity,
            "urgency": request.urgency,
            "justification": request.justification,
            "revenue_at_risk_aed": request.revenue_at_risk_aed,
            "revenue_recoverable_aed": request.revenue_recoverable_aed,
        }
        
        po = db.insert_purchase_order(po_data)
        
        logger.info(
            "draft_purchase_order_success",
            po_id=po["po_id"],
            product_id=request.product_id,
            urgency=request.urgency,
            revenue_at_risk_aed=request.revenue_at_risk_aed,
        )
        
        return DraftPurchaseOrderResponse(
            po_id=po["po_id"],
            product_id=request.product_id,
            product_name=product["product_name"],
            quantity=request.quantity,
            urgency=request.urgency,
            justification=request.justification,
            revenue_at_risk_aed=request.revenue_at_risk_aed,
            revenue_recoverable_aed=request.revenue_recoverable_aed,
            evidence_summary=request.evidence_summary,
            status="pending",
            human_approval_required=True,  # ALWAYS true - never auto-approve
            created_at=po["created_at"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("draft_purchase_order_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
