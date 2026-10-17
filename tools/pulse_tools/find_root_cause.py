"""find_root_cause — SPEC-PULSE-02.

Cross-references a stockout pattern with the AlloyDB replenishment schedule to
identify the supply gap. Returns root cause, confidence, and a MANDATORY
evidence block citing the exact data used.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Request
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.logger import get_logger
from tools.shared.rate_limit import limiter

logger = get_logger("pulse.find_root_cause")
router = APIRouter()

# SPEC-PULSE-02: peak_hour format HH:MM-HH:MM
_PEAK_RE = re.compile(r"^\d{2}:\d{2}-\d{2}:\d{2}$")
# Allowed root_cause enum (SPEC-PULSE-02 §4).
_ROOT_CAUSES = {
    "delivery_timing_mismatch",
    "insufficient_order_quantity",
    "supplier_delay",
    "demand_spike",
    "unknown",
}


def _confidence(incident_count: int, has_schedule: bool) -> str:
    # High: clear pattern (10+) + matching schedule; Medium: 5-9 or partial;
    # Low: minimal data / no schedule.
    if not has_schedule:
        return "Low"
    if incident_count >= 10:
        return "High"
    return "Medium"


def _parse_hhmm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def find_root_cause(
    product_id: str,
    store_id: str,
    peak_hour: str,
    incident_count: int,
    period_hours: int,
) -> dict:
    """
    Cross-references a stockout pattern with the replenishment schedule in
    AlloyDB to identify the root cause of the supply gap. Returns root_cause
    (enum), confidence_level, explanation, a mandatory evidence block, and a
    recommended_action.
    """
    # ── Validation (SPEC-PULSE-02 §4) ────────────────────────────────
    if not _PEAK_RE.match(peak_hour or ""):
        return error("VALIDATION_ERROR", "peak_hour must be HH:MM-HH:MM")
    if incident_count < 5:
        return error("VALIDATION_ERROR", "incident_count must be >= 5")
    if not (1 <= period_hours <= 168):
        return error("VALIDATION_ERROR", "period_hours must be 1..168")

    db = get_alloydb()
    product = db.get_product(product_id)
    if not product:
        return error("NOT_FOUND", f"product {product_id} not found")

    sched = db.get_replenishment(store_id, product_id)
    peak_start = _parse_hhmm(peak_hour.split("-")[0])

    if sched:
        delivery_day = sched["delivery_day"]
        delivery_time = str(sched["delivery_time"])
        qty_per_delivery = int(sched.get("quantity_per_delivery", 0))
        # Gap between the demand peak and the delivery time, in hours.
        try:
            delivery_min = _parse_hhmm(delivery_time[:5])
        except (ValueError, IndexError):
            delivery_min = peak_start
        gap_hours = abs(delivery_min - peak_start) // 60
        # Daily deliveries have effectively no timing gap.
        if delivery_day.lower() == "daily":
            gap_hours = 0

        if qty_per_delivery and qty_per_delivery < incident_count * 2:
            root_cause = "insufficient_order_quantity"
            explanation = (
                f"Each delivery brings {qty_per_delivery} units but demand over the "
                f"window implies ~{incident_count * 2}. Volume, not timing, is the gap."
            )
            recommended = f"Increase delivery quantity for {product['product_name']} to >= {incident_count * 2} units."
        elif gap_hours >= 2:
            root_cause = "delivery_timing_mismatch"
            explanation = (
                f"Delivery arrives {delivery_day} {delivery_time} but demand peaks "
                f"{peak_hour} — a {gap_hours}-hour supply gap."
            )
            recommended = "Switch to an earlier/extra delivery aligned to the morning peak."
        else:
            root_cause = "demand_spike"
            explanation = (
                f"Delivery timing and volume look adequate; the stockouts cluster at "
                f"{peak_hour}, consistent with a demand spike."
            )
            recommended = "Add buffer stock to absorb the peak-window demand spike."
    else:
        delivery_day, delivery_time, gap_hours = "unknown", "unknown", 0
        root_cause = "unknown"
        explanation = (
            f"No replenishment schedule found for {product['product_name']} at "
            f"{store_id}; root cause cannot be confirmed from available data."
        )
        recommended = "Establish a replenishment schedule so the cause can be diagnosed."

    assert root_cause in _ROOT_CAUSES
    confidence = _confidence(incident_count, has_schedule=sched is not None)
    result = {
        "root_cause": root_cause,
        "confidence_level": confidence,
        "explanation": explanation,
        "evidence": {
            "delivery_day": delivery_day,
            "delivery_time": delivery_time,
            "demand_peak_window": peak_hour,
            "gap_hours": gap_hours,
            "data_sources": [
                f"BigQuery incidents table: {incident_count} rows over {period_hours}h",
                f"AlloyDB replenishment_schedule: store={store_id}, product={product_id}",
            ],
        },
        "recommended_action": recommended,
    }
    logger.info("find_root_cause", tool="find_root_cause", product_id=product_id,
                root_cause=root_cause, confidence_level=confidence, status="success")
    return result


class RootCauseRequest(BaseModel):
    product_id: str
    store_id: str
    peak_hour: str
    incident_count: int
    period_hours: int


@router.post("/tools/find-root-cause")
@limiter.limit("20/minute")
async def find_root_cause_endpoint(request: Request, req: RootCauseRequest) -> dict:
    return find_root_cause(
        req.product_id, req.store_id, req.peak_hour, req.incident_count, req.period_hours
    )
