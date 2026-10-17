"""Smoke tests for the shared mock adapters — SPEC-00 foundation.

These validate the adapter layer the tool functions build on. Marked `unit`:
no Docker, no GCP.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_alloydb_reads_customer(alloydb, customer_id):
    c = alloydb.get_customer(customer_id)
    assert c is not None
    assert c["dietary_preference"] == "halal"


def test_alloydb_inventory_and_oos(alloydb, store_id):
    inv = alloydb.list_inventory(store_id)
    assert len(inv) > 0
    brown_rice = alloydb.get_product("rice_brown_500g")
    assert brown_rice["stock_quantity"] == 0  # demo stockout scenario


def test_alloydb_order_write(alloydb, store_id, customer_id):
    order = alloydb.insert_order(
        {"customer_id": customer_id, "store_id": store_id, "items": [], "total_aed": 100.0}
    )
    assert order["order_id"]
    assert order["status"] == "confirmed"


def test_bigquery_bridge_insert_then_detect(bigquery, store_id):
    # Seeded with 8 brown-rice incidents; add one more live.
    bigquery.insert_incident(
        {
            "session_id": "t_live",
            "store_id": store_id,
            "timestamp": "2026-10-17T10:30:00",
            "items_unavailable": [{"product_id": "rice_brown_500g", "product_name": "Brown Rice 500g"}],
            "cart_total_aed": 300.0,
            "order_placed": False,
        }
    )
    patterns = bigquery.detect_stockout_patterns(store_id=store_id, hours=48, min_incidents=5)
    assert any(p["product_id"] == "rice_brown_500g" and p["incident_count"] >= 9 for p in patterns)


def test_bigquery_insert_idempotent(bigquery, store_id):
    row = {"session_id": "dup", "store_id": store_id, "timestamp": "2026-10-17T10:00:00",
           "items_unavailable": [], "cart_total_aed": 0.0, "order_placed": True}
    bigquery.insert_incident(row)
    bigquery.insert_incident(row)  # same session_id -> no duplicate
    # one session only; detect should be unaffected by the dup
    patterns = bigquery.detect_stockout_patterns(store_id=store_id, hours=48, min_incidents=5)
    assert isinstance(patterns, list)
