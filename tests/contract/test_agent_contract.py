"""Contract tests — validate the ARIA /aria/chat response matches the Agent API
shape the frontend consumes, and PULSE /pulse/analyze returns the ops shape.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agents.aria.main import app as aria_app
from agents.pulse.main import app as pulse_app

pytestmark = pytest.mark.contract


def test_aria_chat_contract_shape():
    client = TestClient(aria_app)
    r = client.post(
        "/aria/chat",
        json={
            "customer_id": "sarah_123",
            "store_id": "dubai_marina_01",
            "message": "weekly groceries, family of 4, halal, AED 300",
        },
    )
    assert r.status_code == 200
    d = r.json()
    # Top-level contract keys
    assert set(["reply", "cart", "reasoning", "order", "session_logged"]).issubset(d.keys())
    # cart shape
    assert set(["items", "total_aed", "promotion"]).issubset(d["cart"].keys())
    for item in d["cart"]["items"]:
        assert set(["product_id", "product_name", "quantity", "price_aed", "aisle_ref", "in_stock"]).issubset(item.keys())
    # reasoning step shape
    for step in d["reasoning"]:
        assert step["type"] in ("THOUGHT", "ACTION", "OBSERVATION")
        assert isinstance(step["text"], str)


def test_aria_chat_confirm_places_order():
    client = TestClient(aria_app)
    draft = client.post("/aria/chat", json={"message": "weekly halal groceries"}).json()
    r = client.post("/aria/chat", json={"session_id": draft["session_id"],
                    "message": "confirm", "quote_id": draft["quote_id"]})
    assert r.status_code == 200
    d = r.json()
    assert d["order"]["status"] == "confirmed"
    assert d["session_logged"] is True


def test_pulse_analyze_contract_shape():
    client = TestClient(pulse_app)
    r = client.post("/pulse/analyze", json={"store_id": "dubai_marina_01"})
    assert r.status_code == 200
    d = r.json()
    assert "stockout_alerts" in d and "perishable_alerts" in d
    if d["stockout_alerts"]:
        alert = d["stockout_alerts"][0]
        assert set(["pattern", "root_cause", "prediction", "impact", "purchase_order"]).issubset(alert.keys())
        assert alert["purchase_order"]["status"] == "pending"
        assert alert["purchase_order"]["human_approval_required"] is True
