"""PULSE dashboard data provider — live bridge or static mock.

The dashboard reads operational data through this module. Two sources:

  LIVE (default when the backend package is importable): calls the real PULSE
  tool functions in-process, which read the shared BigQuery incidents bridge.
  Because ARIA's log_session writes to that same in-memory bridge, a session
  ARIA logs shows up here within one dashboard refresh — the closed-loop demo
  moment (ARCHITECTURE.md §10.4).

  STATIC: falls back to mock_data.py if the backend import fails (e.g. the
  dashboard is run standalone without the tools package on the path).

Shapes returned match what pulse_dashboard.py renders, regardless of source.
"""

from __future__ import annotations

import os

STORE_ID = os.getenv("PULSE_STORE_ID", "dubai_marina_01")

# Decide the source once at import. PULSE_FORCE_MOCK=true pins static mock.
_FORCE_MOCK = os.getenv("PULSE_FORCE_MOCK", "").strip().lower() in {"1", "true", "yes"}

_LIVE = False
if not _FORCE_MOCK:
    try:
        from tools.pulse_tools.calculate_impact import calculate_impact
        from tools.pulse_tools.detect_patterns import detect_patterns
        from tools.pulse_tools.draft_purchase_order import draft_purchase_order
        from tools.pulse_tools.execute_perishable_discount import (
            execute_perishable_discount,
        )
        from tools.pulse_tools.find_root_cause import find_root_cause

        _LIVE = True
    except Exception:
        _LIVE = False


def is_live() -> bool:
    return _LIVE


def source_label() -> str:
    return "LIVE" if _LIVE else "MOCK DATA"


# ── Static fallback ──────────────────────────────────────────────────
def _static_stockouts() -> list[dict]:
    import mock_data

    return mock_data.stockout_patterns()


def _static_perishables() -> list[dict]:
    import mock_data

    return mock_data.perishable_alerts()


# ── Live assembly from the real PULSE tools ──────────────────────────
def _live_stockouts() -> list[dict]:
    """Run the PULSE ops cycle and flatten into the dashboard's card shape."""
    out: list[dict] = []
    patterns = detect_patterns(STORE_ID).get("patterns", [])
    for p in patterns:
        rc = find_root_cause(
            p["product_id"], STORE_ID, p["peak_hour"],
            p["incident_count"], p["period_hours"],
        )
        impact = calculate_impact(
            p["product_id"], STORE_ID, p["incident_count"],
            p.get("average_cart_aed", 0.0) or 1.0, p["abandonment_count"], 2,
        )
        po = draft_purchase_order(
            p["product_id"], STORE_ID, 120, "high",
            rc.get("recommended_action", "Restock"),
            impact["revenue_at_risk_aed"], impact["revenue_recoverable_aed"],
            impact["calculation_basis"],
        )
        out.append(
            {
                "product_id": p["product_id"],
                "product_name": p["product_name"],
                "store_id": STORE_ID,
                "incident_count": p["incident_count"],
                "period_hours": p["period_hours"],
                "estimated_revenue_lost_aed": p["estimated_revenue_lost_aed"],
                "peak_hour": p["peak_hour"],
                "abandonment_count": p["abandonment_count"],
                "evidence": p.get("evidence", {}),
                "root_cause": rc.get("explanation", rc.get("root_cause", "")),
                "confidence_level": rc.get("confidence_level", "Medium"),
                "root_cause_evidence": rc.get("evidence", {}),
                "revenue_lost_aed": impact["revenue_lost_aed"],
                "revenue_at_risk_aed": impact["revenue_at_risk_aed"],
                "revenue_recoverable_aed": impact["revenue_recoverable_aed"],
                "calculation_basis": impact["calculation_basis"],
                "po": {
                    "po_id": po["po_id"],
                    "product_id": po["product_id"],
                    "product_name": po["product_name"],
                    "quantity": po["quantity"],
                    "urgency": po["urgency"],
                    "supplier": po.get("evidence_summary", ""),
                    "justification": po["justification"],
                    "revenue_at_risk_aed": po["revenue_at_risk_aed"],
                    "revenue_recoverable_aed": po["revenue_recoverable_aed"],
                    "status": po["status"],
                    "human_approval_required": po["human_approval_required"],
                    "created_at": po["created_at"],
                },
            }
        )
    return out


def _live_perishables() -> list[dict]:
    return execute_perishable_discount(STORE_ID).get("perishable_alerts", [])


# ── Public API used by pulse_dashboard.py ────────────────────────────
def stockout_patterns() -> list[dict]:
    return _live_stockouts() if _LIVE else _static_stockouts()


def perishable_alerts() -> list[dict]:
    return _live_perishables() if _LIVE else _static_perishables()


def summary_metrics() -> dict:
    patterns = stockout_patterns()
    perish = perishable_alerts()
    pos_pending = sum(1 for p in patterns if p["po"]["status"] == "pending")
    return {
        "incidents_48h": sum(p["incident_count"] for p in patterns),
        "incidents_delta": sum(p["incident_count"] for p in patterns),
        "revenue_at_risk_aed": round(
            sum(p["revenue_at_risk_aed"] for p in patterns)
            + sum(a["revenue_at_risk_aed"] for a in perish),
            2,
        ),
        "pos_pending": pos_pending,
    }


# ── Manager approval write-backs (closed loop) ───────────────────────
# In LIVE mode these mutate the shared AlloyDB so the rest of the system
# reacts: an approved perishable discount flips discount_active=True, which
# ARIA then surfaces on its next check_stock (ARCHITECTURE.md perishable loop).
# In static mode they are no-ops (session_state already reflects the choice).
def approve_discount(product_id: str) -> None:
    if not _LIVE:
        return
    try:
        from tools.shared.alloydb_client import get_alloydb

        get_alloydb().set_discount_active(product_id, True)
    except Exception:
        pass


def approve_po(po_id: str) -> None:
    if not _LIVE:
        return
    try:
        from tools.shared.alloydb_client import get_alloydb

        db = get_alloydb()
        po = db._purchase_orders.get(po_id)  # mock in-memory store
        if po is not None:
            po["status"] = "approved"
    except Exception:
        pass


def reject_po(po_id: str) -> None:
    if not _LIVE:
        return
    try:
        from tools.shared.alloydb_client import get_alloydb

        db = get_alloydb()
        po = db._purchase_orders.get(po_id)
        if po is not None:
            po["status"] = "rejected"
    except Exception:
        pass
