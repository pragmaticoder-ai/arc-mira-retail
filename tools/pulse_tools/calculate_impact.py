"""calculate_impact — SPEC-PULSE-04.

Business impact in AED for a confirmed stockout pattern: revenue lost
(historical), at risk (forecast), recoverable (if PO approved today). Must
cite its basis in plain language. Always called before drafting a PO.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.errors import error
from tools.shared.logger import get_logger

logger = get_logger("pulse.calculate_impact")
router = APIRouter()

_MARGIN_PCT = 0.15


def calculate_impact(
    product_id: str,
    store_id: str,
    incident_count: int,
    average_cart_aed: float,
    abandonment_count: int,
    days_to_next_delivery: int,
) -> dict:
    """
    Calculates business impact in AED for a confirmed stockout pattern. Returns
    revenue_lost (historical), revenue_at_risk (forecast), revenue_recoverable
    (if PO approved today), with a plain-language basis. Always call before
    drafting a purchase order.
    """
    if incident_count < 0 or average_cart_aed < 0:
        return error("VALIDATION_ERROR", "counts and amounts must be non-negative")

    abandonment_rate = (abandonment_count / incident_count) if incident_count else 0.0

    revenue_lost = round(incident_count * average_cart_aed * abandonment_rate * _MARGIN_PCT, 2)
    # At risk: projected continued loss until next delivery.
    daily_loss = revenue_lost / max(1, 2)  # over the ~48h observed window → per-day
    revenue_at_risk = round(daily_loss * max(1, days_to_next_delivery), 2)
    # Recoverable: assume approving the PO recovers ~85% of at-risk revenue.
    revenue_recoverable = round(revenue_at_risk * 0.85, 2)

    result = {
        "revenue_lost_aed": revenue_lost,
        "revenue_at_risk_aed": revenue_at_risk,
        "revenue_recoverable_aed": revenue_recoverable,
        "calculation_basis": (
            f"{incident_count} incidents × AED {average_cart_aed:.2f} avg cart × "
            f"{abandonment_rate:.0%} abandonment × {_MARGIN_PCT:.0%} margin; "
            f"at-risk projected over {days_to_next_delivery} day(s) to next delivery."
        ),
        "evidence": {
            "incidents_used": incident_count,
            "average_cart_aed": round(average_cart_aed, 2),
            "abandonment_rate": round(abandonment_rate, 2),
            "formula": "incident_count × avg_cart × abandonment_rate × margin_pct",
        },
    }
    logger.info(
        "calculate_impact",
        tool="calculate_impact",
        product_id=product_id,
        revenue_at_risk_aed=revenue_at_risk,
        status="success",
    )
    return result


class CalculateImpactRequest(BaseModel):
    product_id: str
    store_id: str
    incident_count: int
    average_cart_aed: float
    abandonment_count: int
    days_to_next_delivery: int


@router.post("/tools/calculate-impact")
async def calculate_impact_endpoint(req: CalculateImpactRequest) -> dict:
    return calculate_impact(
        req.product_id, req.store_id, req.incident_count, req.average_cart_aed,
        req.abandonment_count, req.days_to_next_delivery,
    )
