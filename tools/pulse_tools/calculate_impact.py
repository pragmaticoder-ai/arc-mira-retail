"""PULSE tool: calculate_impact

Calculates business impact in AED for stockout patterns.

Spec: specs/SPEC-PULSE-04-calculate_impact.md
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from tools.shared.models import (
    CalculateImpactRequest,
    CalculateImpactResponse,
    ImpactEvidence,
)
from tools.shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/calculate-impact", response_model=CalculateImpactResponse)
async def calculate_impact(request: CalculateImpactRequest):
    """
    Calculate business impact (revenue lost, at risk, recoverable).
    
    Returns:
        CalculateImpactResponse: AED impact figures with evidence
    """
    try:
        # Calculate abandonment rate
        abandonment_rate = request.abandonment_count / max(1, request.incident_count)
        
        # Calculate revenue lost (historical)
        # Formula: incident_count × avg_cart × abandonment_rate × margin_pct
        margin_pct = 0.15
        revenue_lost = request.incident_count * request.average_cart_aed * abandonment_rate * margin_pct
        
        # Calculate revenue at risk (forecast)
        # Assume 7 days of continued pattern if not addressed
        daily_incidents = request.incident_count / 7  # rough daily average
        revenue_at_risk = daily_incidents * 7 * request.average_cart_aed * margin_pct
        
        # Calculate revenue recoverable (if PO approved)
        # Assume 70% recovery rate with expedited restocking
        recovery_rate = 0.70
        days_until_delivery = max(1, request.days_to_next_delivery)
        revenue_recoverable = revenue_at_risk * recovery_rate * (7 - days_until_delivery) / 7
        
        calculation_basis = (
            f"Based on {request.incident_count} incidents over last 7 days, "
            f"average cart AED {request.average_cart_aed:.2f}, "
            f"abandonment rate {abandonment_rate:.1%}, "
            f"15% margin at risk."
        )
        
        logger.info(
            "calculate_impact_success",
            product_id=request.product_id,
            revenue_lost_aed=revenue_lost,
            revenue_at_risk_aed=revenue_at_risk,
            revenue_recoverable_aed=revenue_recoverable,
        )
        
        return CalculateImpactResponse(
            revenue_lost_aed=round(revenue_lost, 2),
            revenue_at_risk_aed=round(revenue_at_risk, 2),
            revenue_recoverable_aed=round(revenue_recoverable, 2),
            calculation_basis=calculation_basis,
            evidence=ImpactEvidence(
                incidents_used=request.incident_count,
                average_cart_aed=request.average_cart_aed,
                abandonment_rate=round(abandonment_rate, 2),
                formula="incident_count × avg_cart × abandonment_rate × margin_pct",
            ),
        )
        
    except Exception as e:
        logger.error("calculate_impact_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
