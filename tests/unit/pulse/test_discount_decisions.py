"""A retry cannot authorize a larger discount than the manager approved."""
from datetime import timedelta
from importlib import import_module

import pytest

from tools.pulse_tools.demand_intelligence import decide_discount
from tools.pulse_tools.execute_perishable_discount import execute_perishable_discount
from tools.shared.alloydb_client import get_alloydb
from tools.shared.clock import today

STORE = "dubai_marina_01"
PRODUCT = "laban_almarai_1l"


@pytest.mark.parametrize("status", ["approved", "rejected"])
@pytest.mark.parametrize("days_later", [1, 3])
def test_discount_retry_preserves_original_decision_and_price(monkeypatch, status, days_later):
    original = decide_discount(PRODUCT, STORE, status)
    before = get_alloydb().get_product_at_store(PRODUCT, STORE)
    module = import_module("tools.pulse_tools.execute_perishable_discount")
    monkeypatch.setattr(module, "today", lambda: today() + timedelta(days=days_later))

    assert decide_discount(PRODUCT, STORE, status) == original
    assert get_alloydb().get_product_at_store(PRODUCT, STORE) == before
    with pytest.raises(ValueError, match="already has a decision"):
        decide_discount(PRODUCT, STORE, "rejected" if status == "approved" else "approved")

    if status == "approved" and days_later == 1:
        proposal = next(p for p in execute_perishable_discount(STORE)["perishable_alerts"]
                        if p["product_id"] == PRODUCT)
        assert proposal["discount_pct"] == original["discount_pct"] == before["discount_pct"]
        assert proposal["discounted_price_aed"] == before["discounted_price_aed"]
