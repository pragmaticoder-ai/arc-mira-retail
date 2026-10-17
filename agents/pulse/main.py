"""PULSE agent HTTP service — Cloud Run entry point.

Exposes POST /pulse/analyze, which runs the operations intelligence cycle and
returns stockout alerts (with root cause, prediction, impact, draft PO) and
perishable discount proposals — the shape the PULSE dashboard consumes.

Mock mode (default) runs a deterministic cycle over the real PULSE tools.
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from tools.pulse_tools.calculate_impact import calculate_impact
from tools.pulse_tools.detect_patterns import detect_patterns
from tools.pulse_tools.draft_purchase_order import draft_purchase_order
from tools.pulse_tools.execute_perishable_discount import execute_perishable_discount
from tools.pulse_tools.find_root_cause import find_root_cause
from tools.pulse_tools.predict_stockout import predict_stockout
from tools.shared.logger import get_logger
from tools.shared.settings import settings

logger = get_logger("pulse.agent")
app = FastAPI(title="ARC PULSE Agent", version="1.0.0")


class AnalyzeRequest(BaseModel):
    store_id: str = "dubai_marina_01"
    hours: int = 48
    min_incidents: int = 5


def _cycle(req: AnalyzeRequest) -> dict:
    """Deterministic PULSE cycle following the system prompt's sequencing."""
    patterns = detect_patterns(req.store_id, req.hours, req.min_incidents)["patterns"]
    alerts = []
    for p in patterns:
        rc = find_root_cause(p["product_id"], req.store_id, p["peak_hour"],
                             p["incident_count"], p["period_hours"])
        pred = predict_stockout(p["product_id"], req.store_id)
        impact = calculate_impact(p["product_id"], req.store_id, p["incident_count"],
                                  p["average_cart_aed"], p["abandonment_count"], 2)
        po = draft_purchase_order(
            p["product_id"], req.store_id, 120, "high",
            rc["recommended_action"], impact["revenue_at_risk_aed"],
            impact["revenue_recoverable_aed"], impact["calculation_basis"],
        )
        alerts.append({
            "pattern": p,
            "root_cause": rc,
            "prediction": pred,
            "impact": impact,
            "purchase_order": po,
        })

    perishable = execute_perishable_discount(req.store_id)["perishable_alerts"]

    logger.info("pulse_cycle", store_id=req.store_id, alerts=len(alerts),
                perishable=len(perishable), status="success")
    return {"stockout_alerts": alerts, "perishable_alerts": perishable}


@app.post("/pulse/analyze")
async def pulse_analyze(req: AnalyzeRequest) -> dict:
    if settings.use_mock:
        return _cycle(req)
    from agents.pulse.agent import get_agent

    get_agent()
    raise NotImplementedError("Real ADK run wiring pending; set USE_MOCK=true.")


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "arc-pulse-agent", "mode": "mock" if settings.use_mock else "live"}
