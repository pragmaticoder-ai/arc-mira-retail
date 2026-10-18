"""Full per-spec unit tests for the 9 ARIA tools (SPEC-ARIA-01..09).

Covers the TC-* cases enumerated in each spec's §7. Mock-mode, no Docker.
"""

from __future__ import annotations

import uuid

import pytest

from tools.aria_tools.apply_promotion import apply_promotion
from tools.aria_tools.build_cart import build_cart
from tools.aria_tools.check_stock import check_stock
from tools.aria_tools.get_customer_context import get_customer_context
from tools.aria_tools.log_session import log_session
from tools.aria_tools.optimize_budget import optimize_budget
from tools.aria_tools.parse_intent import parse_intent
from tools.aria_tools.place_order import place_order
from tools.aria_tools.suggest_substitution import suggest_substitution

pytestmark = pytest.mark.unit


# ══ SPEC-ARIA-01: parse_intent ═══════════════════════════════════════
def test_aria01_full_message():
    r = parse_intent("I need halal groceries for the week, family of 4, under AED 300")
    assert r["dietary_preference"] == "halal"
    assert r["budget_aed"] == 300.0
    assert r["household_size"] == 4
    assert r["urgency"] == "normal"


def test_aria01_vegetarian():
    r = parse_intent("I need vegetarian food for 2 people")
    assert r["dietary_preference"] == "vegetarian"
    assert r["household_size"] == 2


def test_aria01_urgent():
    r = parse_intent("I need milk urgently")
    assert r["urgency"] == "urgent"


def test_aria01_partial_defaults():
    r = parse_intent("I need some groceries")
    assert r["dietary_preference"] == "none"
    assert r["budget_aed"] is None
    assert r["household_size"] is None
    assert r["urgency"] == "normal"


def test_aria01_empty_rejected():
    assert parse_intent("")["error_code"] == "VALIDATION_ERROR"


def test_aria01_too_long_rejected():
    assert parse_intent("a" * 1001)["error_code"] == "VALIDATION_ERROR"


def test_aria01_sql_injection_rejected():
    assert parse_intent("SELECT * FROM inventory; DROP TABLE orders;")["error_code"] == "VALIDATION_ERROR"


# ══ SPEC-ARIA-02: get_customer_context ═══════════════════════════════
def test_aria02_success(customer_id):
    r = get_customer_context(customer_id)
    assert r["name"] == "Sarah"
    assert r["dietary_preference"] == "halal"
    assert r["weekly_budget_aed"] == 300.0


def test_aria02_not_found():
    assert get_customer_context("unknown_999")["error_code"] == "NOT_FOUND"


def test_aria02_empty_id():
    assert get_customer_context("")["error_code"] == "VALIDATION_ERROR"


def test_aria02_orders_capped_at_3(customer_id):
    r = get_customer_context(customer_id)
    assert len(r["last_orders"]) <= 3


def test_aria02_no_orders():
    r = get_customer_context("fatima_789")
    assert r["last_orders"] == []


def test_aria02_invalid_format():
    assert get_customer_context("sarah; DROP TABLE customers;")["error_code"] == "VALIDATION_ERROR"


def test_aria02_budget_positive(customer_id):
    assert get_customer_context(customer_id)["weekly_budget_aed"] > 0


# ══ SPEC-ARIA-03: build_cart ═════════════════════════════════════════
def test_aria03_weekly_halal(store_id):
    r = build_cart("weekly groceries", "halal", 300.0, 4, store_id)
    assert r["items"]
    assert r["total_aed"] <= 300.0


def test_aria03_halal_filter(store_id):
    r = build_cart("weekly groceries", "halal", 300.0, 4, store_id)
    from tools.shared.alloydb_client import get_alloydb
    db = get_alloydb()
    for item in r["items"]:
        p = db.get_product(item["product_id"])
        assert "halal" in p["dietary_flags"]


def test_aria03_total_calculation(store_id):
    r = build_cart("weekly groceries", "halal", 300.0, 4, store_id)
    computed = round(sum(i["price_aed"] * i["quantity"] for i in r["items"]), 2)
    assert computed == r["total_aed"]


def test_aria03_invalid_store():
    assert build_cart("weekly groceries", "halal", 300.0, 4, "nonexistent")["error_code"] == "NOT_FOUND"


def test_aria03_bad_budget(store_id):
    assert build_cart("weekly groceries", "halal", 0, 4, store_id)["error_code"] == "VALIDATION_ERROR"


def test_aria03_household_quantity(store_id):
    small = build_cart("weekly groceries", "halal", 500.0, 1, store_id)
    large = build_cart("weekly groceries", "halal", 500.0, 5, store_id)
    small_q = sum(i["quantity"] for i in small["items"])
    large_q = sum(i["quantity"] for i in large["items"])
    assert large_q >= small_q


# ══ SPEC-ARIA-04: check_stock ════════════════════════════════════════
def test_aria04_in_stock(store_id):
    r = check_stock("milk_almarai_2l", store_id)
    assert r["available"] is True
    assert r["quantity"] > 0
    assert r["aisle_ref"]
    assert r["alternative_stores"] == []


def test_aria04_out_of_stock_with_alternatives(store_id):
    r = check_stock("rice_brown_500g", store_id)
    assert r["available"] is False
    assert len(r["alternative_stores"]) >= 1


def test_aria04_aisle_null_when_unavailable(store_id):
    r = check_stock("rice_brown_500g", store_id)
    assert r["aisle_ref"] is None


def test_aria04_max_3_alternatives(store_id):
    r = check_stock("rice_brown_500g", store_id)
    assert len(r["alternative_stores"]) <= 3


def test_aria04_product_not_found(store_id):
    assert check_stock("nonexistent", store_id)["error_code"] == "NOT_FOUND"


def test_aria04_surfaces_discount(store_id):
    from tools.pulse_tools.demand_intelligence import decide_discount
    assert check_stock("laban_almarai_1l", store_id)["discount_active"] is False
    decide_discount("laban_almarai_1l", store_id, "approved")
    assert check_stock("laban_almarai_1l", store_id)["discount_active"] is True


# ══ SPEC-ARIA-05: suggest_substitution ═══════════════════════════════
def test_aria05_excludes_original(store_id):
    r = suggest_substitution("rice_brown_500g", store_id, "halal", 50.0)
    assert r["substitute_product_id"] != "rice_brown_500g"


def test_aria05_score_range(store_id):
    r = suggest_substitution("rice_brown_500g", store_id, "halal", 50.0)
    assert 0.0 <= r["similarity_score"] <= 1.0


def test_aria05_dietary_respected(store_id):
    r = suggest_substitution("chicken_whole_1kg", store_id, "vegan", 30.0)
    if r.get("substitute_product_id"):
        from tools.shared.alloydb_client import get_alloydb
        p = get_alloydb().get_product(r["substitute_product_id"])
        assert "vegan" in p["dietary_flags"]


def test_aria05_product_not_found(store_id):
    assert suggest_substitution("nope", store_id, "halal", 50.0)["error_code"] == "NOT_FOUND"


def test_aria05_semantic_relevance(store_id):
    # Brown rice should substitute to a grain, never an unrelated dairy drink.
    r = suggest_substitution("rice_brown_500g", store_id, "halal", 50.0)
    from tools.shared.alloydb_client import get_alloydb
    p = get_alloydb().get_product(r["substitute_product_id"])
    assert p["category"] == "grains"


def test_aria05_purchase_history_preference(store_id):
    # Sarah has basmati in history; it should be preferred for brown rice.
    r = suggest_substitution("rice_brown_500g", store_id, "halal", 50.0, customer_id="sarah_123")
    assert r["from_purchase_history"] is True
    assert r["substitute_product_id"] == "rice_basmati_5kg"


# ══ SPEC-ARIA-06: optimize_budget ════════════════════════════════════
def _mk(pid, qty, price):
    return {"product_id": pid, "product_name": pid, "quantity": qty, "price_aed": price, "aisle_ref": "", "in_stock": True}


def test_aria06_already_within():
    cart = [_mk("a", 1, 50.0)]
    r = optimize_budget(cart, 100.0)
    assert r["changes_made"] == []


def test_aria06_reduce_quantity():
    cart = [_mk("a", 10, 12.0), _mk("b", 5, 10.0)]
    r = optimize_budget(cart, 150.0)
    assert r["new_total_aed"] <= 150.0
    assert r["changes_made"]


def test_aria06_not_over_trimmed():
    cart = [_mk("a", 10, 12.0), _mk("b", 5, 10.0)]
    r = optimize_budget(cart, 150.0)
    assert r["new_total_aed"] >= 150.0 * 0.85


def test_aria06_unprocessable_over_trim():
    cart = [_mk("a", 1, 200.0), _mk("b", 1, 150.0)]
    assert optimize_budget(cart, 300.0)["error_code"] == "UNPROCESSABLE"


def test_aria06_empty_cart_rejected():
    assert optimize_budget([], 100.0)["error_code"] == "VALIDATION_ERROR"


def test_aria06_changes_explained():
    cart = [_mk("a", 10, 12.0), _mk("b", 5, 10.0)]
    r = optimize_budget(cart, 150.0)
    for c in r["changes_made"]:
        assert c["action"] in ("reduced_quantity", "removed", "swapped_brand")


# ══ SPEC-ARIA-07: apply_promotion ════════════════════════════════════
def test_aria07_applied(store_id):
    cart = build_cart("weekly groceries", "halal", 300.0, 4, store_id)
    r = apply_promotion(cart["items"], cart["total_aed"], "halal", store_id)
    assert r["promotion_applied"] is True
    assert r["new_total_aed"] < cart["total_aed"]


def test_aria07_none_below_min(store_id):
    cart = [_mk("milk_almarai_2l", 1, 12.0)]
    r = apply_promotion(cart, 12.0, "halal", store_id)
    # dairy saver needs 40; no promo applies
    assert r["promotion_applied"] is False


def test_aria07_expired_not_applied(store_id):
    # promo_expired is active but out of its validity window; never chosen.
    cart = [_mk("milk_almarai_2l", 10, 12.0)]
    r = apply_promotion(cart, 120.0, "halal", store_id)
    assert r["promotion_id"] != "promo_expired"


def test_aria07_max_uses_respected(store_id):
    cart = [_mk("milk_almarai_2l", 10, 12.0)]
    r = apply_promotion(cart, 120.0, "halal", store_id)
    assert r["promotion_id"] != "promo_maxed"


def test_aria07_highest_value_selected(store_id):
    # dairy saver (15%) beats rice 10% for a dairy+grains cart
    cart = [_mk("milk_almarai_2l", 5, 12.0)]
    r = apply_promotion(cart, 60.0, "none", store_id)
    assert r["promotion_id"] == "promo_dairy_saver"


def test_aria07_preview_does_not_consume_usage(store_id):
    from tools.shared.alloydb_client import get_alloydb
    db = get_alloydb()
    before = next(p["times_applied"] for p in db.list_active_promotions(store_id) if p["promotion_id"] == "promo_dairy_saver")
    apply_promotion([_mk("milk_almarai_2l", 5, 12.0)], 60.0, "none", store_id)
    after = next(p["times_applied"] for p in db.list_active_promotions(store_id) if p["promotion_id"] == "promo_dairy_saver")
    assert after == before


# ══ SPEC-ARIA-08: place_order ════════════════════════════════════════
def test_aria08_success(store_id, customer_id):
    cart = [_mk("milk_almarai_2l", 1, 12.0)]
    r = place_order(customer_id, store_id, cart, None, 12.0)
    assert r["order_id"]
    assert r["status"] == "confirmed"


def test_aria08_duplicate_idempotent(store_id, customer_id):
    cart = [_mk("milk_almarai_2l", 1, 12.0)]
    a = place_order(customer_id, store_id, cart, None, 12.0)
    b = place_order(customer_id, store_id, cart, None, 12.0)
    assert a["order_id"] == b["order_id"]


def test_aria08_total_mismatch(store_id, customer_id):
    cart = [_mk("milk_almarai_2l", 1, 12.0)]
    assert place_order(customer_id, store_id, cart, None, 999.0)["error_code"] == "VALIDATION_ERROR"


def test_aria08_stock_decremented(store_id, customer_id):
    from tools.shared.alloydb_client import get_alloydb
    db = get_alloydb()
    before = db.get_product_at_store("milk_almarai_2l", store_id)["stock_quantity"]
    place_order(customer_id, store_id, [_mk("milk_almarai_2l", 2, 12.0)], None, 24.0)
    after = db.get_product_at_store("milk_almarai_2l", store_id)["stock_quantity"]
    assert after == before - 2


def test_aria08_insufficient_stock(store_id, customer_id):
    cart = [_mk("milk_almarai_2l", 99999, 12.0)]
    assert place_order(customer_id, store_id, cart, None, 12.0 * 99999)["error_code"] == "VALIDATION_ERROR"


def test_aria08_delivery_future(store_id, customer_id):
    r = place_order(customer_id, store_id, [_mk("milk_almarai_2l", 1, 12.0)], None, 12.0)
    assert r["estimated_delivery_window"]


def test_aria08_empty_cart(store_id, customer_id):
    assert place_order(customer_id, store_id, [], None, 0.0)["error_code"] == "VALIDATION_ERROR"


# ══ SPEC-ARIA-09: log_session ════════════════════════════════════════
def test_aria09_success(store_id, customer_id):
    sid = str(uuid.uuid4())
    r = log_session(sid, customer_id, store_id, [], [], [], None, 0.0, 0.0, 300.0, "positive", True)
    assert r["logged"] is True
    assert r["session_id"] == sid


def test_aria09_no_order(store_id, customer_id):
    sid = str(uuid.uuid4())
    r = log_session(sid, customer_id, store_id, [], [], [], None, 0.0, 0.0, 300.0, "negative", False, "budget exceeded")
    assert r["logged"] is True


def test_aria09_empty_arrays(store_id, customer_id):
    sid = str(uuid.uuid4())
    r = log_session(sid, customer_id, store_id, [], [], [], None, 0.0, 0.0, 300.0, "neutral", True)
    assert r["logged"] is True


def test_aria09_invalid_uuid(store_id, customer_id):
    assert log_session("not-a-uuid", customer_id, store_id, [], [], [], None, 0.0, 0.0, 300.0, "positive", True)["error_code"] == "VALIDATION_ERROR"


def test_aria09_invalid_sentiment(store_id, customer_id):
    sid = str(uuid.uuid4())
    assert log_session(sid, customer_id, store_id, [], [], [], None, 0.0, 0.0, 300.0, "happy", True)["error_code"] == "VALIDATION_ERROR"
