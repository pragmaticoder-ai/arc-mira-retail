"""Bridge test — the architectural heart of ARC.

ARIA logs a session to the BigQuery incidents bridge; PULSE detects the
resulting stockout pattern. Runs in mock mode (in-memory bridge), so it's a
`unit`-marked test, not Docker integration — it proves the loop logic.
"""

from __future__ import annotations

import uuid

import pytest

from tools.aria_tools.log_session import log_session
from tools.pulse_tools.detect_patterns import detect_patterns

pytestmark = pytest.mark.unit


def test_aria_write_surfaces_in_pulse(bigquery, store_id, customer_id):
    # Baseline: seeded brown-rice incidents already present.
    before = detect_patterns(store_id)["patterns"]
    before_count = next((p["incident_count"] for p in before if p["product_id"] == "rice_brown_500g"), 0)
    assert before_count >= 5

    # ARIA logs a new session where brown rice was unavailable and abandoned.
    res = log_session(
        str(uuid.uuid4()), customer_id, store_id,
        items_ordered=[], items_unavailable=[{"product_id": "rice_brown_500g", "product_name": "Brown Rice 500g"}],
        substitutions=[], promotion_id=None, promotion_saving_aed=0.0,
        cart_total_aed=300.0, budget_aed=300.0, sentiment="negative",
        order_placed=False, abandonment_reason="item_unavailable",
    )
    assert res["logged"] is True

    # PULSE sees the incremented count.
    after = detect_patterns(store_id)["patterns"]
    after_count = next(p["incident_count"] for p in after if p["product_id"] == "rice_brown_500g")
    assert after_count == before_count + 1


def test_log_session_idempotent(bigquery, store_id, customer_id):
    row = dict(
        customer_id=customer_id, store_id=store_id,
        items_ordered=[], items_unavailable=[{"product_id": "rice_brown_500g", "product_name": "Brown Rice 500g"}],
        substitutions=[], promotion_id=None, promotion_saving_aed=0.0,
        cart_total_aed=100.0, budget_aed=300.0, sentiment="neutral", order_placed=False,
    )
    same_id = str(uuid.uuid4())
    log_session(same_id, **row)
    c1 = next(p["incident_count"] for p in detect_patterns(store_id)["patterns"] if p["product_id"] == "rice_brown_500g")
    log_session(same_id, **row)  # same session_id → idempotent
    c2 = next(p["incident_count"] for p in detect_patterns(store_id)["patterns"] if p["product_id"] == "rice_brown_500g")
    assert c1 == c2
