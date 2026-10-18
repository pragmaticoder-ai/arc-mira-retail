"""Shared local PULSE data. Fail visibly instead of silently faking approvals."""
from __future__ import annotations

import os

from tools.pulse_tools.calculate_impact import calculate_impact
from tools.pulse_tools.demand_intelligence import decide_demand as decide_demand
from tools.pulse_tools.demand_intelligence import (
    decide_discount,
    demand_insights,
)
from tools.pulse_tools.detect_patterns import detect_patterns
from tools.pulse_tools.draft_purchase_order import draft_purchase_order
from tools.pulse_tools.execute_perishable_discount import execute_perishable_discount
from tools.pulse_tools.find_root_cause import find_root_cause
from tools.shared.alloydb_client import get_alloydb
from tools.shared.settings import settings

STORE_ID = os.getenv("PULSE_STORE_ID", "dubai_marina_01")


def is_live() -> bool:
    return not settings.use_mock or bool(settings.arc_state_db and settings.arc_bridge_db)


def source_label() -> str:
    if not settings.use_mock:
        return "GOOGLE CLOUD · POSTGRESQL + BIGQUERY"
    return "SHARED LOCAL DATA · RULES" if is_live() else "PROCESS MEMORY · RULES"


def stockout_patterns(store_id: str = STORE_ID, hours: int = 48) -> list[dict]:
    out = []
    for p in detect_patterns(store_id, hours).get("patterns", []):
        rc = find_root_cause(p["product_id"], store_id, p["peak_hour"], p["incident_count"], hours)
        impact = calculate_impact(p["product_id"], store_id, p["incident_count"],
                                  p.get("average_cart_aed", 0) or 1, p["abandonment_count"], 2)
        product = get_alloydb().get_product_at_store(p["product_id"], store_id)
        if product is None:
            continue
        qty = max(product["reorder_threshold"], p["incident_count"])
        po = draft_purchase_order(p["product_id"], store_id, qty, "high",
            rc.get("recommended_action", "Review replenishment"), impact["revenue_at_risk_aed"],
            impact["revenue_recoverable_aed"], impact["calculation_basis"])
        out.append({**p, **impact, "root_cause": rc.get("explanation", "Unknown"),
            "confidence_level": rc.get("confidence_level", "Low"),
            "root_cause_evidence": rc.get("evidence", {}), "po": {**po, "supplier": po.get("evidence_summary", "")}})
    return out


def perishable_alerts(store_id: str = STORE_ID) -> list[dict]:
    return execute_perishable_discount(store_id).get("perishable_alerts", [])


def summary_metrics(store_id: str = STORE_ID, hours: int = 48) -> dict:
    patterns = stockout_patterns(store_id, hours)
    insights = demand_insights(store_id, hours)
    return {"incidents_48h": sum(p["incident_count"] for p in patterns),
            "unresolved": sum(i["counts"]["unresolved"] for i in insights),
            "compromises": sum(i["counts"]["compromise"] for i in insights),
            "pos_pending": sum(p["po"]["status"] == "pending" for p in patterns)}


def approve_discount(product_id: str, store_id: str = STORE_ID) -> dict:
    return decide_discount(product_id, store_id, "approved")


def reject_discount(product_id: str, store_id: str = STORE_ID) -> dict:
    return decide_discount(product_id, store_id, "rejected")


def approve_po(po_id: str) -> dict:
    return get_alloydb().decide_purchase_order(po_id, "approved")


def reject_po(po_id: str) -> dict:
    return get_alloydb().decide_purchase_order(po_id, "rejected")


def google_summary(store_id: str, hours: int) -> str:
    import httpx

    url=os.getenv("PULSE_AGENT_URL", "http://127.0.0.1:8002")
    headers={}
    if os.getenv("K_SERVICE"):
        from google.auth.transport.requests import Request
        from google.oauth2.id_token import fetch_id_token

        headers["Authorization"]="Bearer "+fetch_id_token(Request(),url)
    response = httpx.post(url + "/pulse/analyze",headers=headers,
                          json={"store_id": store_id, "hours": hours}, timeout=120)
    response.raise_for_status()
    return response.json()["summary"]
