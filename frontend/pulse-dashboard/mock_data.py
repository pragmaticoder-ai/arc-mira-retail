"""Mock PULSE data — demo stand-in for the real backend.

NOTE: This file is the FRONTEND engineer's demo stand-in so the dashboard can
run offline. The backend engineer owns the real PULSE tools (tools/pulse_tools/)
and the live data layer. Shapes here mirror AGENT_CONTRACTS.md exactly so the
dashboard swaps to the real agent with no reshaping:
  - detect_patterns() -> patterns[]
  - find_root_cause() -> root_cause + evidence
  - calculate_impact() -> revenue_lost/at_risk/recoverable
  - draft_purchase_order() -> pending PO
  - execute_perishable_discount() -> perishable_alerts[]
"""

from __future__ import annotations

from datetime import datetime, timedelta

STORE_ID = "dubai_marina_01"
STORE_NAME = "MIRA Dubai Marina"


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


# ── detect_patterns() + find_root_cause() + calculate_impact() + PO ──────
# One stockout pattern: the brown-rice-at-Dubai-Marina demo scenario.
def stockout_patterns() -> list[dict]:
    now = datetime(2026, 10, 17, 11, 0, 0)
    return [
        {
            "product_id": "rice_brown_500g",
            "product_name": "Brown Rice 500g",
            "store_id": STORE_ID,
            "incident_count": 8,
            "period_hours": 48,
            "estimated_revenue_lost_aed": 3200.0,
            "peak_hour": "10:00–12:00",
            "abandonment_count": 3,
            "evidence": {
                "first_incident": _iso(now - timedelta(hours=46)),
                "last_incident": _iso(now - timedelta(hours=2)),
                "sample_session_ids": ["sess_a91", "sess_b42", "sess_c77"],
                "substitution_acceptance_rate": 0.62,
            },
            # find_root_cause()
            "root_cause": (
                "Delivery lands Tuesday 14:00 but demand peaks Mon–Wed 10:00–12:00. "
                "Shelf empties ~20h before the next replenishment."
            ),
            "confidence_level": "High",
            "root_cause_evidence": {
                "delivery_day": "Tuesday",
                "delivery_time": "14:00",
                "demand_peak_window": "Mon–Wed 10:00–12:00",
                "gap_hours": 20,
                "data_sources": [
                    "BigQuery incidents: 8 rows, Oct 15–17 2026",
                    "AlloyDB replenishment_schedule: store=dubai_marina_01, product=rice_brown_500g",
                ],
            },
            # calculate_impact()
            "revenue_lost_aed": 3200.0,
            "revenue_at_risk_aed": 1800.0,
            "revenue_recoverable_aed": 1500.0,
            "calculation_basis": (
                "8 incidents × AED 285 avg cart × 0.62 abandonment × 0.15 margin, "
                "plus 7-day forecast at risk."
            ),
            # draft_purchase_order()
            "po": {
                "po_id": "po_demo_0001",
                "product_id": "rice_brown_500g",
                "product_name": "Brown Rice 500g",
                "quantity": 120,
                "urgency": "high",
                "supplier": "Organic Larder (sup_004)",
                "justification": (
                    "Restock ahead of Mon–Wed demand peak; current schedule leaves "
                    "a 20h gap. Recommend a mid-week top-up delivery."
                ),
                "revenue_at_risk_aed": 1800.0,
                "revenue_recoverable_aed": 1500.0,
                "status": "pending",
                "human_approval_required": True,
                "created_at": _iso(now),
            },
        }
    ]


# ── execute_perishable_discount() -> perishable_alerts[] ─────────────────
def perishable_alerts() -> list[dict]:
    return [
        {
            "product_id": "laban_almarai_1l",
            "product_name": "Almarai Laban 1L",
            "store_id": STORE_ID,
            "stock_quantity": 48,
            "expiry_date": "2026-10-19",
            "days_to_expiry": 2,
            "daily_sales_rate": 8.5,
            "projected_sell_through": 17,
            "units_at_risk": 31,
            "revenue_at_risk_aed": 248.0,
            "discount_pct": 25.0,
            "discounted_price_aed": 6.0,
            "revenue_recoverable_aed": 186.0,
            "evidence": {
                "data_source": "BigQuery incidents — 7-day velocity",
                "expiry_source": "AlloyDB inventory.expiry_date",
                "trigger_formula": "days_to_expiry × daily_sales_rate < stock_quantity",
            },
            "status": "pending",
            "human_approval_required": True,
        }
    ]


def summary_metrics() -> dict:
    patterns = stockout_patterns()
    perish = perishable_alerts()
    return {
        "incidents_48h": sum(p["incident_count"] for p in patterns),
        "incidents_delta": 8,
        "revenue_at_risk_aed": sum(p["revenue_at_risk_aed"] for p in patterns)
        + sum(a["revenue_at_risk_aed"] for a in perish),
        "pos_pending": sum(1 for p in patterns if p["po"]["status"] == "pending"),
    }
