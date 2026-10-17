"""Full per-spec unit tests for the 6 PULSE tools (SPEC-PULSE-01..06).

Covers the TC-* cases enumerated in each spec's §7. Mock-mode, no Docker.
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


# ══ SPEC-PULSE-01: detect_patterns ═══════════════════════════════════
def test_pulse01_finds_brown_rice(store_id):
    ids = [p["product_id"] for p in detect_patterns(store_id)["patterns"]]
    assert "rice_brown_500g" in ids


def test_pulse01_sorted_by_revenue(store_id):
    revs = [p["estimated_revenue_lost_aed"] for p in detect_patterns(store_id)["patterns"]]
    assert revs == sorted(revs, reverse=True)


def test_pulse01_threshold(store_id):
    assert detect_patterns(store_id, min_incidents=100)["patterns"] == []


def test_pulse01_abandonment_count(store_id):
    p = detect_patterns(store_id)["patterns"][0]
    assert p["abandonment_count"] >= 0


def test_pulse01_evidence_populated(store_id):
    p = detect_patterns(store_id)["patterns"][0]
    ev = p["evidence"]
    assert ev["first_incident"] and ev["last_incident"]
    assert ev["sample_session_ids"]
    assert 0.0 <= ev["substitution_acceptance_rate"] <= 1.0


def test_pulse01_hours_out_of_range(store_id):
    assert detect_patterns(store_id, hours=1000)["error_code"] == "VALIDATION_ERROR"


def test_pulse01_empty_store():
    assert detect_patterns("empty_store_xyz")["patterns"] == []


# ══ SPEC-PULSE-02: find_root_cause ═══════════════════════════════════
def test_pulse02_timing_mismatch(store_id):
    r = find_root_cause("rice_brown_500g", store_id, "10:00-12:00", 8, 48)
    assert r["root_cause"] == "delivery_timing_mismatch"
    assert r["evidence"]["gap_hours"] >= 2


def test_pulse02_no_schedule_unknown(store_id):
    # pasta has no replenishment schedule in the mock
    r = find_root_cause("pasta_barilla_500g", store_id, "10:00-12:00", 8, 48)
    assert r["root_cause"] == "unknown"
    assert r["confidence_level"] == "Low"


def test_pulse02_evidence_two_sources(store_id):
    r = find_root_cause("rice_brown_500g", store_id, "10:00-12:00", 8, 48)
    assert len(r["evidence"]["data_sources"]) >= 2


def test_pulse02_confidence_medium(store_id):
    r = find_root_cause("rice_brown_500g", store_id, "10:00-12:00", 8, 48)
    assert r["confidence_level"] == "Medium"  # 8 incidents (5-9)


def test_pulse02_invalid_peak_hour(store_id):
    assert find_root_cause("rice_brown_500g", store_id, "morning", 8, 48)["error_code"] == "VALIDATION_ERROR"


def test_pulse02_recommended_action(store_id):
    r = find_root_cause("rice_brown_500g", store_id, "10:00-12:00", 8, 48)
    assert r["recommended_action"].strip()


def test_pulse02_product_not_found(store_id):
    assert find_root_cause("nope", store_id, "10:00-12:00", 8, 48)["error_code"] == "NOT_FOUND"


def test_pulse02_incident_below_min(store_id):
    assert find_root_cause("rice_brown_500g", store_id, "10:00-12:00", 3, 48)["error_code"] == "VALIDATION_ERROR"


# ══ SPEC-PULSE-03: predict_stockout ══════════════════════════════════
def test_pulse03_high_confidence_surfaced(store_id):
    r = predict_stockout("rice_brown_500g", store_id)
    assert r["surfaced"] is True
    assert r["predicted_stockout_date"] is not None


def test_pulse03_confidence_range(store_id):
    r = predict_stockout("rice_brown_500g", store_id)
    assert 0.0 <= r["confidence"] <= 1.0


def test_pulse03_days_non_negative(store_id):
    r = predict_stockout("rice_brown_500g", store_id)
    assert r["days_until_stockout"] >= 0


def test_pulse03_evidence(store_id):
    r = predict_stockout("rice_brown_500g", store_id)
    ev = r["evidence"]
    assert ev["model"] and ev["training_period"] and ev["data_points_used"]


def test_pulse03_forecast_days_range(store_id):
    assert predict_stockout("rice_brown_500g", store_id, forecast_days=99)["error_code"] == "VALIDATION_ERROR"


# ══ SPEC-PULSE-04: calculate_impact ══════════════════════════════════
def test_pulse04_formula(store_id):
    # 23 incidents, avg 220, abandon 5 -> lost = 23*220*(5/23)*0.15 = 165.0
    r = calculate_impact("rice_brown_500g", store_id, 23, 220.0, 5, 2)
    assert abs(r["revenue_lost_aed"] - 165.0) < 0.5


def test_pulse04_recoverable_bounded(store_id):
    r = calculate_impact("rice_brown_500g", store_id, 23, 220.0, 5, 2)
    assert r["revenue_recoverable_aed"] <= r["revenue_at_risk_aed"]


def test_pulse04_abandonment_rate(store_id):
    r = calculate_impact("rice_brown_500g", store_id, 10, 220.0, 3, 2)
    assert r["evidence"]["abandonment_rate"] == 0.30


def test_pulse04_invalid_abandonment(store_id):
    assert calculate_impact("rice_brown_500g", store_id, 5, 220.0, 10, 2)["error_code"] == "VALIDATION_ERROR"


def test_pulse04_basis_readable(store_id):
    r = calculate_impact("rice_brown_500g", store_id, 23, 220.0, 5, 2)
    assert "incidents" in r["calculation_basis"]
    assert r["evidence"]["formula"]


def test_pulse04_zero_abandonment(store_id):
    r = calculate_impact("rice_brown_500g", store_id, 10, 220.0, 0, 2)
    assert r["revenue_lost_aed"] == 0.0


# ══ SPEC-PULSE-05: draft_purchase_order ══════════════════════════════
def test_pulse05_success(store_id):
    r = draft_purchase_order("rice_brown_500g", store_id, 120, "critical", "restock", 2961.0, 3200.0, "evidence")
    assert r["status"] == "pending"
    assert r["human_approval_required"] is True


def test_pulse05_always_pending(store_id):
    r = draft_purchase_order("rice_brown_500g", store_id, 50, "high", "x", 100.0, 80.0, "e")
    assert r["status"] == "pending"


def test_pulse05_idempotent_24h(store_id):
    a = draft_purchase_order("rice_brown_500g", store_id, 120, "high", "restock", 100.0, 80.0, "e")
    b = draft_purchase_order("rice_brown_500g", store_id, 120, "high", "restock", 100.0, 80.0, "e")
    assert a["po_id"] == b["po_id"]


def test_pulse05_invalid_quantity(store_id):
    assert draft_purchase_order("rice_brown_500g", store_id, 0, "high", "x", 1.0, 1.0, "e")["error_code"] == "VALIDATION_ERROR"
    assert draft_purchase_order("rice_brown_500g", store_id, 99999, "high", "x", 1.0, 1.0, "e")["error_code"] == "VALIDATION_ERROR"


def test_pulse05_justification_too_long(store_id):
    assert draft_purchase_order("rice_brown_500g", store_id, 50, "high", "x" * 1001, 1.0, 1.0, "e")["error_code"] == "VALIDATION_ERROR"


def test_pulse05_po_id_format(store_id):
    r = draft_purchase_order("rice_brown_500g", store_id, 50, "high", "restock", 100.0, 80.0, "e")
    assert r["po_id"].startswith("PO-")


# ══ SPEC-PULSE-06: execute_perishable_discount ═══════════════════════
def test_pulse06_trigger_fires(store_id):
    ids = [a["product_id"] for a in execute_perishable_discount(store_id)["perishable_alerts"]]
    assert "laban_almarai_1l" in ids


def test_pulse06_tiers_valid(store_id):
    for a in execute_perishable_discount(store_id)["perishable_alerts"]:
        assert a["discount_pct"] in (15.0, 25.0, 40.0)


def test_pulse06_laban_exact_values(store_id):
    laban = next(a for a in execute_perishable_discount(store_id)["perishable_alerts"] if a["product_id"] == "laban_almarai_1l")
    assert laban["days_to_expiry"] == 2
    assert laban["discount_pct"] == 25.0
    assert laban["projected_sell_through"] == 17
    assert laban["discounted_price_aed"] == 6.0
    assert laban["evidence"]["trigger_formula"] == "2 × 8.5 = 17 < 48 units in stock"


def test_pulse06_always_pending(store_id):
    for a in execute_perishable_discount(store_id)["perishable_alerts"]:
        assert a["status"] == "pending"
        assert a["human_approval_required"] is True


def test_pulse06_recoverable_bounded(store_id):
    for a in execute_perishable_discount(store_id)["perishable_alerts"]:
        assert a["revenue_recoverable_aed"] <= a["revenue_at_risk_aed"]


def test_pulse06_empty_store_no_error():
    r = execute_perishable_discount("empty_store_xyz")
    assert r["perishable_alerts"] == []
