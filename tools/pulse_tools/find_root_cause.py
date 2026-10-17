"""PULSE tool: find_root_cause

Cross-references stockout patterns with replenishment schedules
to identify root causes of supply gaps.

Spec: specs/SPEC-PULSE-02-find_root_cause.md
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from tools.shared.models import (
    FindRootCauseRequest,
    FindRootCauseResponse,
    RootCauseEvidence,
)
from tools.shared.alloydb_client import get_alloydb
from tools.shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/find-root-cause", response_model=FindRootCauseResponse)
async def find_root_cause(request: FindRootCauseRequest):
    """
    Analyze root cause of a stockout pattern.
    
    Returns:
        FindRootCauseResponse: root cause, confidence, explanation, evidence
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
        
        # Mock implementation: the demo brown rice scenario
        # Real implementation would query replenishment_schedule table
        if request.product_id == "rice_brown_500g" and request.store_id == "dubai_marina_01":
            root_cause = "Supply-demand timing gap"
            confidence = "High"
            explanation = (
                "Deliveries arrive Tuesday 2PM, but demand peaks Monday-Wednesday 10AM-12PM. "
                "This creates a 4-hour supply gap during peak shopping hours."
            )
            evidence = RootCauseEvidence(
                delivery_day="Tuesday",
                delivery_time="14:00",
                demand_peak_window="Monday-Wednesday 10:00-12:00",
                gap_hours=4,
                data_sources=[
                    f"BigQuery incidents table: {request.incident_count} rows, last {request.period_hours} hours",
                    f"AlloyDB replenishment_schedule: store={request.store_id}, product={request.product_id}",
                ],
            )
            recommended_action = "Expedite next delivery by 6 hours or add Wednesday morning delivery slot"
        else:
            # Generic response for other products
            root_cause = "Insufficient reorder threshold"
            confidence = "Medium"
            explanation = (
                f"Current stock ({product.get('stock_quantity', 0)}) fell below demand. "
                f"Reorder threshold is {product.get('reorder_threshold', 10)}."
            )
            evidence = RootCauseEvidence(
                delivery_day="Unknown",
                delivery_time="Unknown",
                demand_peak_window=request.peak_hour,
                gap_hours=0,
                data_sources=[
                    f"AlloyDB inventory: product={request.product_id}",
                ],
            )
            recommended_action = f"Lower reorder threshold from {product.get('reorder_threshold', 10)} to {max(5, product.get('reorder_threshold', 10) - 5)}"
        
        logger.info(
            "find_root_cause_success",
            product_id=request.product_id,
            root_cause=root_cause,
            confidence=confidence,
        )
        
        return FindRootCauseResponse(
            root_cause=root_cause,
            confidence_level=confidence,
            explanation=explanation,
            evidence=evidence,
            recommended_action=recommended_action,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("find_root_cause_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
