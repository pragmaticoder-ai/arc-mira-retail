"""Unit tests for the 9 ARIA tools (SPEC-ARIA-01..09).

Mock-mode, no Docker. Covers the key cases from each spec's test section.
"""

from __future__ import annotations

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


# ── parse_intent (SPEC-ARIA-01) ──────────────────────────────────────
def test_parse_intent_full_message():
    r = parse_intent("Weekly groceries, family of 4, halal, AED 300")
    assert r["dietary_preference"] == "halal"
    assert r["budget_aed"] == 300.0
    assert r["household_size"] == 4
    assert r["urgency"] == "normal"


def test_parse_intent_urgent():
    r = parse_intent("I need milk urgently")
    assert r["urgency"] == "urgent"


def test_parse_intent_empty_rejected():
    r = parse_intent("")
    assert r.get("error") and r["error_code"] == "VALIDATION_ERROR"


def test_parse_intent_too_long_rejected():
    r = parse_intent("a" * 1001)
    assert r.get("error") and r["error_code"] == "VALIDATION_ERROR"


def test_parse_intent_injection_rejected():
    r = parse_intent("SELECT * FROM inventory; DROP TABLE orders;")
    assert r.get("error") and r["error_code"] == "VALIDATION_ERROR"


# ── get_customer_context (SPEC-ARIA-02) ──────────────────────────────
def test_get_customer_context_found(customer_id):
    r = get_customer_context(customer_id)
    assert r["name"] == "Sarah"
    assert r["dietary_preference"] == "halal"


def test_get_customer_context_not_found():
    r = get_customer_context("nope_000")
    assert r.get("error") and r["error_code"] == "NOT_FOUND"


# ── build_cart (SPEC-ARIA-03) ────────────────────────────────────────
def test_build_cart_halal_within_budget(store_id):
    r = build_cart("weekly groceries", "halal", 300.0, 4, store_id)
    assert r["items"], "expected items"
    assert r["total_aed"] <= 300.0


def test_build_cart_invalid_store():
    r = build_cart("weekly groceries", "halal", 300.0, 4, "no_store")
    assert r.get("error") and r["error_code"] == "NOT_FOUND"


def test_build_cart_bad_budget(store_id):
    r = build_cart("weekly groceries", "halal", 0, 4, store_id)
    assert r.get("error") and r["error_code"] == "VALIDATION_ERROR"


def test_build_cart_total_matches_items(store_id):
    r = build_cart("weekly groceries", "halal", 300.0, 4, store_id)
    computed = round(sum(i["price_aed"] * i["quantity"] for i in r["items"]), 2)
    assert computed == r["total_aed"]


# ── check_stock (SPEC-ARIA-04) ───────────────────────────────────────
def test_check_stock_out_of_stock(store_id):
    r = check_stock("rice_brown_500g", store_id)
    assert r["available"] is False


def test_check_stock_surfaces_discount(store_id):
    r = check_stock("laban_almarai_1l", store_id)
    assert r["available"] is True
    assert r["discount_active"] is True


# ── suggest_substitution (SPEC-ARIA-05) ──────────────────────────────
def test_suggest_substitution_excludes_original(store_id):
    r = suggest_substitution("rice_brown_500g", store_id, "halal", 50.0)
    assert r["substitute_product_id"] != "rice_brown_500g"


def test_suggest_substitution_score_range(store_id):
    r = suggest_substitution("rice_brown_500g", store_id, "halal", 50.0)
    assert 0.0 <= r["similarity_score"] <= 1.0


def test_suggest_substitution_product_not_found(store_id):
    r = suggest_substitution("nope", store_id, "halal", 50.0)
    assert r.get("error") and r["error_code"] == "NOT_FOUND"


# ── optimize_budget (SPEC-ARIA-06) ───────────────────────────────────
def test_optimize_budget_brings_within_target():
    cart = [
        {"product_id": "a", "product_name": "A", "quantity": 1, "price_aed": 50.0, "aisle_ref": "", "in_stock": True},
        {"product_id": "b", "product_name": "B", "quantity": 1, "price_aed": 40.0, "aisle_ref": "", "in_stock": True},
    ]
    r = optimize_budget(cart, 60.0)
    assert r["new_total_aed"] <= 60.0
    assert r["changes_made"]


# ── apply_promotion (SPEC-ARIA-07) ───────────────────────────────────
def test_apply_promotion_dairy(store_id):
    cart = build_cart("weekly groceries", "halal", 300.0, 4, store_id)
    r = apply_promotion(cart["items"], cart["total_aed"], "halal", store_id)
    # Dairy saver should apply (cart has milk, total > 40)
    assert r["promotion_applied"] is True
    assert r["new_total_aed"] < cart["total_aed"]


# ── place_order (SPEC-ARIA-08) ───────────────────────────────────────
def test_place_order_success(store_id, customer_id):
    cart = [{"product_id": "milk_almarai_2l", "product_name": "Milk", "quantity": 1, "price_aed": 12.0, "aisle_ref": "A2", "in_stock": True}]
    r = place_order(customer_id, store_id, cart, None, 12.0)
    assert r["order_id"]
    assert r["status"] == "confirmed"


def test_place_order_empty_cart(store_id, customer_id):
    r = place_order(customer_id, store_id, [], None, 0.0)
    assert r.get("error") and r["error_code"] == "VALIDATION_ERROR"


# ── log_session (SPEC-ARIA-09) ───────────────────────────────────────
def test_log_session_writes_bridge(store_id, customer_id):
    r = log_session("sess_x", customer_id, store_id, [], [], [], None, 0.0, 0.0, 300.0, "neutral", False)
    assert r["logged"] is True
    assert r["session_id"] == "sess_x"
