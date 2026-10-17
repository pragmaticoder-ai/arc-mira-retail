"""detect_patterns — SPEC-PULSE-01.

Reads the BigQuery incidents bridge for products with >= min_incidents
stockouts in the window, ranked by estimated revenue impact. The starting
point for all PULSE analysis. Attaches an evidence block to each pattern.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.bigquery_client import get_bigquery
from tools.shared.errors import error
from tools.shared.logger import get_logger

logger = get_logger("pulse.detect_patterns")
router = APIRouter()


def detect_patterns(store_id: str, hours: int = 48, min_incidents: int = 5) -> dict:
    """
    Queries BigQuery incidents for products with min_incidents+ stockout
    incidents in the window, ranked by estimated revenue impact in AED.
    Always call this first — it is the starting point for all PULSE analysis.
    """
    # ── Validation (SPEC-PULSE-01 §4) ────────────────────────────────
    if not (store_id or "").strip():
        return error("VALIDATION_ERROR", "store_id is required")
    if not (1 <= hours <= 168):
        return error("VALIDATION_ERROR", "hours must be 1..168")
    if not (1 <= min_incidents <= 100):
        return error("VALIDATION_ERROR", "min_incidents must be 1..100")

    bq = get_bigquery()
    raw = bq.detect_stockout_patterns(store_id=store_id, hours=hours, min_incidents=min_incidents)

    patterns = []
    for p in raw:
        patterns.append(
            {
                "product_id": p["product_id"],
                "product_name": p["product_name"],
                "store_id": store_id,
                "incident_count": p["incident_count"],
                "period_hours": hours,
                "estimated_revenue_lost_aed": p["estimated_revenue_lost_aed"],
                "peak_hour": p.get("peak_hour", "10:00-12:00"),
                "abandonment_count": p.get("abandonment_count", 0),
                "average_cart_aed": p.get("average_cart_aed", 0.0),
                "evidence": p.get("evidence", {}),
            }
        )
    patterns.sort(key=lambda x: x["estimated_revenue_lost_aed"], reverse=True)

    logger.info("detect_patterns", tool="detect_patterns", store_id=store_id,
                patterns_found=len(patterns), hours=hours, status="success")
    return {"patterns": patterns}


class DetectPatternsRequest(BaseModel):
    store_id: str
    hours: int = 48
    min_incidents: int = 5


@router.post("/tools/detect-patterns")
async def detect_patterns_endpoint(req: DetectPatternsRequest) -> dict:
    return detect_patterns(req.store_id, req.hours, req.min_incidents)
