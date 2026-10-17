"""calculate_impact — SPEC-PULSE-04.

Business impact in AED for a confirmed stockout pattern: revenue lost
(historical), at risk (forecast), recoverable (if PO approved today). Must
cite its basis in plain language. Always called before drafting a PO.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from tools.shared.errors import error
from tools.shared.logger import get_logger
from tools.shared.rate_limit import limiter

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
    # ── Validation (SPEC-PULSE-04 §4) ────────────────────────────────
    if incident_count < 1:
        return error("VALIDATION_ERROR", "incident_count must be >= 1")
    if average_cart_aed <= 0:
        return error("VALIDATION_ERROR", "average_cart_aed must be > 0")
    if abandonment_count < 0 or abandonment_count > incident_count:
        return error("VALIDATION_ERROR", "abandonment_count must be 0..incident_count")
    if days_to_next_delivery < 0:
        return error("VALIDATION_ERROR", "days_to_next_delivery must be >= 0")

    abandonment_rate = abandonment_count / incident_count

    # revenue_lost (historical, last 48h window) — SPEC-PULSE-04 §3 step 3.
    revenue_lost = round(incident_count * average_cart_aed * abandonment_rate * _MARGIN_PCT, 2)

    # revenue_at_risk (next 7 days if unresolved) — step 4.
    daily_incident_rate = incident_count / 2.0  # per 48h period
    revenue_at_risk = round(
        daily_incident_rate * 7 * average_cart_aed * abandonment_rate * _MARGIN_PCT, 2
    )

    # revenue_recoverable — step 5. Approving today delivers in days_to_next;
    # we recover the fraction of the 7-day horizon remaining after delivery.
    lead = min(days_to_next_delivery, 7)
    revenue_recoverable = round(revenue_at_risk * (7 - lead) / 7, 2)
    revenue_recoverable = min(revenue_recoverable, revenue_at_risk)  # never exceed at-risk

    result = {
        "revenue_lost_aed": revenue_lost,
        "revenue_at_risk_aed": revenue_at_risk,
        "revenue_recoverable_aed": revenue_recoverable,
        "calculation_basis": (
            f"{incident_count} incidents × AED {average_cart_aed:.2f} avg cart × "
            f"{abandonment_rate:.2f} abandonment × {_MARGIN_PCT:.2f} margin = "
            f"AED {revenue_lost:.2f} lost; at-risk projected over 7 days, "
            f"recoverable after {lead}-day delivery lead."
        ),
        "evidence": {
            "incidents_used": incident_count,
            "average_cart_aed": round(average_cart_aed, 2),
            "abandonment_rate": round(abandonment_rate, 2),
            "formula": "incident_count × avg_cart_aed × abandonment_rate × margin_pct",
        },
    }
    logger.info("calculate_impact", tool="calculate_impact", product_id=product_id,
                revenue_lost=revenue_lost, revenue_at_risk=revenue_at_risk, status="success")
    return result


class CalculateImpactRequest(BaseModel):
    product_id: str
    store_id: str
    incident_count: int
    average_cart_aed: float
    abandonment_count: int
    days_to_next_delivery: int


@router.post("/tools/calculate-impact")
@limiter.limit("20/minute")
async def calculate_impact_endpoint(request: Request, req: CalculateImpactRequest) -> dict:
    return calculate_impact(
        req.product_id, req.store_id, req.incident_count, req.average_cart_aed,
        req.abandonment_count, req.days_to_next_delivery,
    )
