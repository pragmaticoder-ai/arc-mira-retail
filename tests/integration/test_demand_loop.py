"""Behavioral regressions for checkout, explicit intent, and shared local state."""
from __future__ import annotations

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from agents.aria.main import app
from scripts.evaluate_demand import evaluate
from tools.aria_tools.build_cart import build_cart
from tools.aria_tools.place_order import place_order
from tools.pulse_tools.demand_intelligence import (
    decide_demand,
    decide_discount,
    demand_insights,
)
from tools.pulse_tools.detect_patterns import detect_patterns
from tools.shared.alloydb_client import (
    SqliteAlloyDBClient,
    get_alloydb,
)
from tools.shared.bigquery_client import SqliteBigQueryClient
from tools.shared.pricing import quote_cart

STORE = "dubai_marina_01"


def chat(**body):
    response = TestClient(app).post("/aria/chat", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def confirm(draft):
    return chat(session_id=draft["session_id"], message="confirm", quote_id=draft["quote_id"])


def test_compromise_remains_visible_after_a_successful_sale():
    before = detect_patterns(STORE)["patterns"][0]["incident_count"]
    draft = chat(message="Weekly halal groceries family of 4 AED 300 include brown rice")
    feedback = chat(session_id=draft["session_id"], message="Okay this time, but brown rice next week", product_id="rice_brown_500g")
    assert feedback["demand_signals"][0]["outcome"] == "compromise"
    assert any(i["substituted"] for i in feedback["cart"]["items"])
    completed = confirm(feedback)
    assert completed["order"]["status"] == "confirmed"
    assert completed["session_logged"] is True
    assert detect_patterns(STORE)["patterns"][0]["incident_count"] == before + 1
    insight = demand_insights(STORE)[0]
    event = next(e for e in insight["evidence"] if e["session_id"] == draft["session_id"])
    assert event["outcome"] == "compromise" and event["order_placed"] is True
    repeated = confirm(feedback)
    assert repeated["order"]["order_id"] == completed["order"]["order_id"]


def test_transfer_reaches_next_customer_and_monitors_observed_fulfillment():
    insight = demand_insights(STORE)[0]
    decision = decide_demand(insight["proposal_key"], STORE, "transfer")
    after_transfer = get_alloydb().get_product_at_store("rice_brown_500g", STORE)["stock_quantity"]
    assert after_transfer == decision["quantity"]
    assert decide_demand(insight["proposal_key"], STORE, "transfer") == decision
    assert get_alloydb().get_product_at_store("rice_brown_500g", STORE)["stock_quantity"] == after_transfer
    draft = chat(message="Brown rice please, AED 30")
    assert draft["substitution_offers"] == []
    done = confirm(draft)
    assert done["order"] and done["demand_signals"][0]["outcome"] == "fulfilled"
    monitor = demand_insights(STORE)[0]["outcome_monitor"]
    assert monitor["after_sessions"] == 1 and monitor["after"]["fulfilled"] == 1
    assert "not a causal" in monitor["note"]


def test_satisfied_substitute_does_not_count_as_unresolved():
    before = demand_insights(STORE)[0]["counts"]["unresolved"]
    draft = chat(message="Brown rice AED 100")
    feedback = chat(session_id=draft["session_id"], message="This works for me", feedback="satisfied", product_id="rice_brown_500g")
    assert feedback["demand_signals"][0]["outcome"] == "satisfied"
    assert demand_insights(STORE)[0]["counts"]["unresolved"] == before


def test_rejection_and_cancellation_record_unmet_need_without_order():
    draft = chat(message="Brown rice AED 100")
    rejected = chat(session_id=draft["session_id"], message="No thanks", feedback="rejected", product_id="rice_brown_500g")
    assert rejected["cart"]["items"] == []
    closed = chat(session_id=draft["session_id"], message="yes but cancel the order")
    assert closed["order"] is None and closed["session_logged"]
    assert closed["demand_signals"][0]["outcome"] == "abandoned"
    assert get_alloydb()._orders == {}


def test_constraints_override_profile_and_small_budget_never_overflows():
    draft = chat(message="Vegan groceries only, no meat or dairy, budget AED 20")
    assert draft["cart"]["total_aed"] <= 20
    for item in draft["cart"]["items"]:
        assert "vegan" in get_alloydb().get_product(item["product_id"])["dietary_flags"]
    assert build_cart("weekly groceries", "halal", 1, 4, STORE)["total_aed"] <= 1


def test_budget_excluded_requested_product_is_not_recorded_as_fulfilled():
    draft = chat(message="Milk AED 1")
    assert draft["cart"]["items"] == [] and draft["demand_signals"] == []


def test_confirmation_requires_quote_and_orders_current_manual_basket():
    client = TestClient(app)
    assert client.post('/aria/chat', json={"message": "confirm"}).status_code == 400
    draft = chat(message="milk AED 100")
    assert chat(session_id=draft["session_id"], message="confirm")["order"] is None
    updated = chat(session_id=draft["session_id"], message="confirm", quote_id=draft["quote_id"],
                   cart=[{"product_id": "eggs_dozen", "quantity": 2, "price_aed": .01}])
    assert updated["order"] is None and updated["cart"]["total_aed"] == 26
    done = confirm(updated)
    order = next(iter(get_alloydb()._orders.values()))
    assert done["order"]["total_aed"] == 26 and order["items"][0]["product_id"] == "eggs_dozen"


@pytest.mark.parametrize("quantity", [-1, 0, 1.5, True, "1"])
def test_invalid_quantities_never_mutate_inventory(quantity):
    db = get_alloydb()
    before = db.get_product_at_store("milk_almarai_2l", STORE)["stock_quantity"]
    result = place_order("sarah_123", STORE, [{"product_id": "milk_almarai_2l", "quantity": quantity, "price_aed": -12}], None, 12)
    assert result["error"]
    assert db.get_product_at_store("milk_almarai_2l", STORE)["stock_quantity"] == before


@pytest.mark.parametrize("promotion", [None, "promo_dairy_saver"])
def test_forged_prices_or_discounts_are_rejected(promotion):
    result = place_order("sarah_123", STORE, [{"product_id": "milk_almarai_2l", "quantity": 5, "price_aed": .01}], promotion, .01)
    assert result["error"]


def test_repeated_product_quantities_are_checked_together():
    item = {"product_id": "milk_almarai_2l", "quantity": 30, "price_aed": 12}
    assert place_order("sarah_123", STORE, [item, item], None, 720)["error"]
    assert get_alloydb().get_product_at_store("milk_almarai_2l", STORE)["stock_quantity"] == 40


def test_promotion_consumes_usage_once_at_checkout():
    db = get_alloydb()
    items = [{"product_id": "milk_almarai_2l", "quantity": 5}]
    quote = quote_cart(items, STORE, "halal")
    promo = quote["promotion"]["promotion_id"]
    before = next(p["times_applied"] for p in db.list_active_promotions(STORE) if p["promotion_id"] == promo)
    for _ in range(2):
        quote_cart(items, STORE, "halal")
    assert next(p["times_applied"] for p in db.list_active_promotions(STORE) if p["promotion_id"] == promo) == before
    for _ in range(2):
        assert place_order("sarah_123", STORE, quote["items"], promo, quote["total_aed"], "same_checkout")["order_id"]
    assert next(p["times_applied"] for p in db.list_active_promotions(STORE) if p["promotion_id"] == promo) == before + 1


def test_missing_profiles_and_invalid_session_ids_are_validation_errors():
    client = TestClient(app, raise_server_exceptions=False)
    assert client.post('/aria/chat', json={"message": "confirm", "customer_id": "missing"}).status_code == 400
    assert client.post('/aria/chat', json={"message": "milk", "session_id": "not-a-uuid"}).status_code == 422


def test_discount_is_inactive_until_persisted_manager_approval():
    db = get_alloydb()
    assert not db.get_product_at_store("laban_almarai_1l", STORE)["discount_active"]
    decide_discount("laban_almarai_1l", STORE, "approved")
    draft = chat(message="laban AED 20")
    assert draft["cart"]["items"][0]["price_aed"] == 6
    with pytest.raises(ValueError):
        decide_discount("laban_almarai_1l", STORE, "rejected")


def test_purchase_order_decision_survives_refresh():
    db = get_alloydb()
    original = db.insert_purchase_order({"product_id": "rice_brown_500g", "store_id": STORE, "quantity": 10})
    db.decide_purchase_order(original["po_id"], "approved")
    again = db.insert_purchase_order({"product_id": "rice_brown_500g", "store_id": STORE, "quantity": 10})
    assert again["po_id"] == original["po_id"] and again["status"] == "approved"


def test_sqlite_rolls_back_whole_checkout_on_write_failure(tmp_path, monkeypatch):
    import tools.shared.alloydb_client as module
    db = SqliteAlloyDBClient(str(tmp_path / 'state.sqlite'))
    monkeypatch.setattr(module, '_client', db)
    def fail(_):
        raise RuntimeError("Disk write failed")
    monkeypatch.setattr(db, 'insert_order', fail)
    with pytest.raises(RuntimeError):
        place_order("sarah_123", STORE, [{"product_id": "milk_almarai_2l", "quantity": 1}], None, 12)
    reader = SqliteAlloyDBClient(str(tmp_path / 'state.sqlite'))
    assert reader.get_product_at_store("milk_almarai_2l", STORE)["stock_quantity"] == 40


def test_concurrent_checkouts_cannot_oversell(tmp_path, monkeypatch):
    import tools.shared.alloydb_client as module
    db = SqliteAlloyDBClient(str(tmp_path / 'state.sqlite'))
    monkeypatch.setattr(module, '_client', db)
    def checkout(key):
        return place_order("sarah_123", STORE, [{"product_id": "milk_almarai_2l", "quantity": 30}], None, 360, key)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(checkout, ['a', 'b']))
    assert sum('order_id' in r for r in results) == 1
    assert db.get_product_at_store('milk_almarai_2l', STORE)['stock_quantity'] == 10


def test_separate_processes_share_incidents_approvals_and_inventory(tmp_path):
    env = {**os.environ, "ARC_BRIDGE_DB": str(tmp_path / 'incidents.sqlite'),
           "ARC_STATE_DB": str(tmp_path / 'state.sqlite'), "USE_MOCK": "true"}
    shopper = '''from fastapi.testclient import TestClient
from agents.aria.main import app
c=TestClient(app)
d=c.post('/aria/chat',json={'message':'brown rice AED 100'}).json()
d=c.post('/aria/chat',json={'session_id':d['session_id'],'message':'Fine this time, next week brown rice'}).json()
assert d['demand_signals'][0]['outcome']=='compromise'
'''
    manager = '''from tools.pulse_tools.demand_intelligence import demand_insights,decide_demand,decide_discount
p=demand_insights('dubai_marina_01')[0]
assert p['counts']['compromise']==5
decide_demand(p['proposal_key'],'dubai_marina_01','transfer')
decide_discount('laban_almarai_1l','dubai_marina_01','approved')
'''
    next_shopper = '''from tools.shared.alloydb_client import get_alloydb
from tools.shared.bigquery_client import get_bigquery
db=get_alloydb()
assert db.get_product_at_store('rice_brown_500g','dubai_marina_01')['stock_quantity']>0
assert db.get_product_at_store('laban_almarai_1l','dubai_marina_01')['discount_active']
assert len(get_bigquery().list_incidents('dubai_marina_01'))==9
'''
    for code in (shopper, manager, next_shopper):
        process = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, timeout=20)
        assert process.returncode == 0, process.stdout + process.stderr


def test_feedback_evaluation_reports_measured_results_with_limitations():
    report = evaluate()
    assert report['rules_correct'] > report['baseline_correct']
    assert report['explicit_compromises_detected'] == 5
    assert 'not held-out' in report['dataset']


def test_sqlite_session_update_is_one_incident(tmp_path):
    db = SqliteBigQueryClient(str(tmp_path / 'incidents.sqlite'))
    row = {"session_id": "test", "store_id": STORE, "timestamp": "2026-10-18T12:00:00+04:00", "order_placed": False}
    db.insert_incident(row)
    db.insert_incident({**row, "order_placed": True})
    rows = [r for r in db.list_incidents(STORE) if r['session_id'] == 'test']
    assert len(rows) == 1 and rows[0]['order_placed'] is True


def test_session_quote_survives_adapter_restart(tmp_path, monkeypatch):
    import tools.shared.alloydb_client as module
    path = str(tmp_path / 'state.sqlite')
    monkeypatch.setattr(module, '_client', SqliteAlloyDBClient(path))
    draft = chat(message='milk AED 100')
    monkeypatch.setattr(module, '_client', SqliteAlloyDBClient(path))
    done = confirm(draft)
    monkeypatch.setattr(module, '_client', SqliteAlloyDBClient(path))
    assert confirm(draft)['order']['order_id'] == done['order']['order_id']
    assert get_alloydb().get_product_at_store('milk_almarai_2l', STORE)['stock_quantity'] == 39


def test_stale_quote_requires_review_after_manager_discount():
    draft = chat(message='laban AED 20')
    assert draft['cart']['total_aed'] == 8
    decide_discount('laban_almarai_1l', STORE, 'approved')
    updated = confirm(draft)
    assert updated['order'] is None and updated['cart']['total_aed'] == 6
    assert updated['quote_id'] != draft['quote_id']
    assert confirm(updated)['order']['total_aed'] == 6


def test_no_dairy_constraint_survives_manual_basket_edit():
    draft = chat(message='Weekly groceries no dairy AED 100')
    r = TestClient(app).post('/aria/chat', json={'session_id': draft['session_id'], 'message': 'confirm',
                         'cart': [{'product_id': 'milk_almarai_2l', 'quantity': 1}]})
    assert r.status_code == 400
    assert get_alloydb()._orders == {}


def test_substitution_feedback_preserves_unsynced_manual_items():
    draft = chat(message='Brown rice AED 100')
    feedback = chat(session_id=draft['session_id'], message='Okay this time', feedback='compromise',
                    product_id='rice_brown_500g', cart=[{'product_id': 'eggs_dozen', 'quantity': 1}])
    assert any(i['product_id'] == 'eggs_dozen' for i in feedback['cart']['items'])
    assert any(i['substituted'] for i in feedback['cart']['items'])
