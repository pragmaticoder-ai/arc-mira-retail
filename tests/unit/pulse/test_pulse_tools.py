"""Unit tests for the 6 PULSE tools (SPEC-PULSE-01..06).

Mock-mode, no Docker. Covers key cases incl. the SPEC-PULSE-06 perishable
trigger invariants.
"""

from __future__ import annotations

import pytest

from tools.pulse_tools.calculate_impact import calculate_impact
from tools.pulse_tools.detect_patterns import detect_patterns
from tools.pulse_tools.draft_purchase_order import draft_purchase_order
from tools.pulse_tools.execute_perishable_discount import execute_perishable_discount
from tools.pulse_tools.find_root_cause import find_root_cause
from tools.pulse_tools.predict_stockout import predict_stockout

pytestmark = pytest.mark.unit


# ── detect_patterns (SPEC-PULSE-01) ──────────────────────────────────
def test_detect_patterns_finds_brown_rice(store_id):
    r = detect_patterns(store_id)
    ids = [p["product_id"] for p in r["patterns"]]
    assert "rice_brown_500g" in ids


def test_detect_patterns_ranked_by_revenue(store_id):
    r = detect_patterns(store_id)
    revs = [p["estimated_revenue_lost_aed"] for p in r["patterns"]]
    assert revs == sorted(revs, reverse=True)


def test_detect_patterns_respects_min_incidents(store_id):
    r = detect_patterns(store_id, min_incidents=100)
    assert r["patterns"] == []


# ── find_root_cause (SPEC-PULSE-02) ──────────────────────────────────
def test_find_root_cause_has_evidence(store_id):
    r = find_root_cause("rice_brown_500g", store_id, "10:00–12:00", 8, 48)
    assert r["confidence_level"] in ("High", "Medium", "Low")
    assert r["evidence"]["data_sources"]  # mandatory evidence block


def test_find_root_cause_confidence_medium(store_id):
    r = find_root_cause("rice_brown_500g", store_id, "10:00–12:00", 8, 48)
    assert r["confidence_level"] == "Medium"  # 5-9 incidents


def test_find_root_cause_product_not_found(store_id):
    r = find_root_cause("nope", store_id, "10:00–12:00", 8, 48)
    assert r.get("error") and r["error_code"] == "NOT_FOUND"


# ── predict_stockout (SPEC-PULSE-03) ─────────────────────────────────
def test_predict_stockout_surfaces_above_threshold(store_id):
    r = predict_stockout("rice_brown_500g", store_id)
    assert r["surfaced"] is True
    assert r["confidence"] >= 0.70


# ── calculate_impact (SPEC-PULSE-04) ─────────────────────────────────
def test_calculate_impact_recoverable_bounded(store_id):
    r = calculate_impact("rice_brown_500g", store_id, 8, 285.0, 3, 2)
    assert r["revenue_recoverable_aed"] <= r["revenue_at_risk_aed"]
    assert "formula" in r["evidence"]


# ── draft_purchase_order (SPEC-PULSE-05) ─────────────────────────────
def test_draft_po_is_pending_and_requires_approval(store_id):
    r = draft_purchase_order("rice_brown_500g", store_id, 120, "high", "restock", 500.0, 400.0, "evidence")
    assert r["status"] == "pending"
    assert r["human_approval_required"] is True


def test_draft_po_bad_quantity(store_id):
    r = draft_purchase_order("rice_brown_500g", store_id, 0, "high", "x", 1.0, 1.0, "e")
    assert r.get("error") and r["error_code"] == "VALIDATION_ERROR"


# ── execute_perishable_discount (SPEC-PULSE-06) ──────────────────────
def test_perishable_trigger_fires_for_laban(store_id):
    r = execute_perishable_discount(store_id)
    ids = [a["product_id"] for a in r["perishable_alerts"]]
    assert "laban_almarai_1l" in ids


def test_perishable_tiers_valid(store_id):
    r = execute_perishable_discount(store_id)
    for a in r["perishable_alerts"]:
        assert a["discount_pct"] in (15.0, 25.0, 40.0)


def test_perishable_laban_exact_values(store_id):
    r = execute_perishable_discount(store_id)
    laban = next(a for a in r["perishable_alerts"] if a["product_id"] == "laban_almarai_1l")
    assert laban["days_to_expiry"] == 2
    assert laban["discount_pct"] == 25.0
    assert laban["projected_sell_through"] == 17
    assert laban["evidence"]["trigger_formula"] == "2 × 8.5 = 17 < 48 units in stock"


def test_perishable_always_pending_and_approval(store_id):
    r = execute_perishable_discount(store_id)
    for a in r["perishable_alerts"]:
        assert a["status"] == "pending"
        assert a["human_approval_required"] is True


def test_perishable_recoverable_bounded(store_id):
    r = execute_perishable_discount(store_id)
    for a in r["perishable_alerts"]:
        assert a["revenue_recoverable_aed"] <= a["revenue_at_risk_aed"]
