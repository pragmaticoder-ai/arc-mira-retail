"""NFR tests — rate limiting and error-shape contract (SPEC §9).

Verifies the per-endpoint rate limit is wired (returns 429 when exceeded) and
that tool error responses follow the standard shape from AGENT_CONTRACTS.md.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.contract


def _aria_client():
    from tools.aria_tools.main import app
    return TestClient(app)


def test_place_order_rate_limit_10_per_min():
    """place_order is limited to 10/minute (SPEC-ARIA-08 §9)."""
    client = _aria_client()
    # 10 allowed, 11th should be 429.
    body = {"customer_id": "sarah_123", "store_id": "dubai_marina_01",
            "cart": [{"product_id": "milk_almarai_2l", "product_name": "Milk",
                      "quantity": 1, "price_aed": 12.0, "aisle_ref": "A2", "in_stock": True}],
            "total_aed": 12.0}
    statuses = [client.post("/tools/place-order", json=body).status_code for _ in range(12)]
    assert 429 in statuses, f"expected a 429 among {statuses}"


def test_error_response_shape():
    """Tool validation errors follow the standard contract shape."""
    client = _aria_client()
    r = client.post("/tools/parse-intent", json={"customer_message": ""})
    d = r.json()
    assert d["error"] is True
    assert set(["error_code", "error_message", "retry_suggested"]).issubset(d.keys())
