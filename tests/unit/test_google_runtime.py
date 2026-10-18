"""Google mode preserves authoritative checkout and cannot select SQLite."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


def test_google_mode_ignores_stale_sqlite_setting(monkeypatch):
    import tools.shared.alloydb_client as adapter
    import tools.shared.postgres_client as postgres

    sentinel = object()
    monkeypatch.setattr(
        adapter,
        "settings",
        SimpleNamespace(use_mock=False, arc_state_db="stale.sqlite"),
    )
    monkeypatch.setattr(postgres, "PostgresClient", lambda: sentinel)
    assert adapter.get_alloydb() is sentinel


@pytest.mark.parametrize("message", ["one milk", "Please offer milk"])
def test_live_plan_is_repriced_and_requires_quote_confirmation(monkeypatch, message):
    import agents.aria.main as aria
    import agents.google_runtime as runtime

    monkeypatch.setattr(aria, "settings", SimpleNamespace(use_mock=False))
    monkeypatch.setattr(
        runtime,
        "plan_shopping",
        lambda *args: runtime.ShoppingPlan(
            action="update_cart",
            reply="Here is the milk you requested.",
            dietary="halal",
            budget=30,
            household=1,
            items=[runtime.BasketItem(product_id="milk_almarai_2l", quantity=1)],
            requested_ids=["milk_almarai_2l"],
        ),
    )
    client = TestClient(aria.app)
    draft = client.post("/aria/chat", json={"message": message}).json()
    assert draft["mode"] == "google"
    assert draft["cart"]["total_aed"] == 12
    assert draft["order"] is None
    stale = client.post(
        "/aria/chat", json={"message": "confirm", "session_id": draft["session_id"]}
    ).json()
    assert stale["order"] is None
    placed = client.post(
        "/aria/chat",
        json={
            "message": "confirm",
            "session_id": draft["session_id"],
            "quote_id": draft["quote_id"],
        },
    ).json()
    assert placed["order"]["status"] == "confirmed"


def test_live_plan_cannot_bypass_diet_or_stock(monkeypatch):
    import agents.aria.main as aria
    import agents.google_runtime as runtime

    monkeypatch.setattr(aria, "settings", SimpleNamespace(use_mock=False))
    monkeypatch.setattr(
        runtime,
        "plan_shopping",
        lambda *args: runtime.ShoppingPlan(
            action="update_cart",
            reply="",
            dietary="vegan",
            budget=100,
            household=1,
            items=[runtime.BasketItem(product_id="chicken_whole_1kg", quantity=1)],
        ),
    )
    result = TestClient(aria.app).post("/aria/chat", json={"message": "vegan dinner"})
    assert result.status_code == 400


def test_substitution_verifier_rejects_invented_catalog_id(monkeypatch):
    import tools.shared.substitution_match as matcher

    monkeypatch.setattr(
        matcher,
        "get_llm",
        lambda: SimpleNamespace(
            generate=lambda *args, **kwargs: (
                '{"product_id":"invented","explanation":""}'
            )
        ),
    )
    with pytest.raises(ValueError, match="outside"):
        matcher.choose_substitute(
            {"product_id": "rice", "product_name": "Brown rice", "category": "grains"},
            [{"product_id": "basmati", "product_name": "Basmati rice"}],
        )


@pytest.mark.parametrize("action", ["answer", "clarify"])
def test_questions_preserve_cart_quote_constraints_and_analytics(monkeypatch, action):
    import agents.aria.main as aria
    import agents.google_runtime as runtime
    from tools.shared.alloydb_client import get_alloydb

    monkeypatch.setattr(aria, "settings", SimpleNamespace(use_mock=False))
    monkeypatch.setattr(
        runtime,
        "plan_shopping",
        lambda *args: runtime.ShoppingPlan(
            action="update_cart",
            reply="Here is your milk.",
            dietary="halal",
            budget=30,
            household=1,
            items=[runtime.BasketItem(product_id="milk_almarai_2l", quantity=1)],
        ),
    )
    client = TestClient(aria.app)
    draft = client.post("/aria/chat", json={"message": "Add one milk"}).json()
    original = get_alloydb().get_session(draft["session_id"])

    def fail_logging(*args, **kwargs):
        pytest.fail("An informational turn must not create a demand/checkout event")

    monkeypatch.setattr(aria, "log_session", fail_logging)
    monkeypatch.setattr(
        runtime,
        "plan_shopping",
        lambda *args: runtime.ShoppingPlan(
            action=action,
            reply="Milk costs AED 12.",
            dietary="vegan",
            budget=999,
            household=20,
            items=[runtime.BasketItem(product_id="rice_basmati_5kg", quantity=1)],
            excluded_ids=["milk_almarai_2l"],
        ),
    )
    result = client.post(
        "/aria/chat",
        json={
            "session_id": draft["session_id"],
            "message": "How much does the milk cost?",
        },
    )
    assert result.status_code == 200
    data = result.json()
    assert data["reply"] == "Milk costs AED 12."
    assert data["cart_changed"] is False
    assert data["cart"] == draft["cart"]
    assert data["quote_id"] == draft["quote_id"]
    state = get_alloydb().get_session(draft["session_id"])
    for key in (
        "cart",
        "quote_id",
        "dietary",
        "budget",
        "household",
        "excluded_ids",
        "demand_signals",
    ):
        assert state.get(key) == original.get(key)
    assert state["conversation"][-1]["text"] == "Milk costs AED 12."


def test_greeting_does_not_create_a_quote(monkeypatch):
    import agents.aria.main as aria
    import agents.google_runtime as runtime

    monkeypatch.setattr(aria, "settings", SimpleNamespace(use_mock=False))
    monkeypatch.setattr(
        runtime,
        "plan_shopping",
        lambda *args: runtime.ShoppingPlan(
            action="answer",
            reply="Hello! How can I help?",
            dietary="halal",
            budget=300,
            household=4,
        ),
    )
    data = TestClient(aria.app).post("/aria/chat", json={"message": "Hi"}).json()
    assert data["reply"] == "Hello! How can I help?"
    assert data["quote_id"] is None
    assert data["cart"]["items"] == []
    assert not data["session_logged"]
    assert data["cart_changed"] is False


def test_invalid_planner_basket_is_corrected_before_state_changes(monkeypatch):
    import agents.aria.main as aria
    import agents.google_runtime as runtime

    seen = []

    def propose(message, state, catalog):
        seen.append(state)
        if len(seen) == 1:
            return runtime.ShoppingPlan(
                action="update_cart",
                reply="Bad proposal",
                dietary="vegan",
                budget=300,
                household=4,
                items=[runtime.BasketItem(product_id="chicken_whole_1kg", quantity=1)],
            )
        assert state.get("planner_validation_feedback")
        assert state["cart"]["items"] == []
        return runtime.ShoppingPlan(
            action="update_cart",
            reply="A corrected basket.",
            dietary="halal",
            budget=300,
            household=4,
            items=[runtime.BasketItem(product_id="milk_almarai_2l", quantity=2)],
        )

    monkeypatch.setattr(aria, "settings", SimpleNamespace(use_mock=False))
    monkeypatch.setattr(runtime, "plan_shopping", propose)
    result = TestClient(aria.app).post(
        "/aria/chat", json={"message": "Weekly groceries for a family of 4, AED 300."}
    )
    assert result.status_code == 200
    assert len(seen) == 2
    assert result.json()["cart"]["items"][0]["product_id"] == "milk_almarai_2l"
    assert result.json()["cart"]["total_aed"] <= 300


def test_weekly_reply_uses_validated_total_and_does_not_replace_missing_brown_rice(
    monkeypatch,
):
    import agents.aria.main as aria
    import agents.google_runtime as runtime

    monkeypatch.setattr(aria, "settings", SimpleNamespace(use_mock=False))
    monkeypatch.setattr(
        runtime,
        "plan_shopping",
        lambda *args: runtime.ShoppingPlan(
            action="update_cart",
            reply="Brown rice included. Total AED 299.98.",
            dietary="halal",
            budget=300,
            household=4,
            items=[
                runtime.BasketItem(product_id="rice_basmati_5kg", quantity=1),
                runtime.BasketItem(product_id="milk_almarai_2l", quantity=2),
            ],
        ),
    )
    monkeypatch.setattr(
        aria,
        "suggest_substitution",
        lambda *args: {
            "substitute_product_id": "rice_basmati_5kg",
            "name": "India Gate Basmati Rice 5kg",
        },
    )
    result = TestClient(aria.app).post(
        "/aria/chat",
        json={
            "message": "Weekly halal groceries, family of 4, AED 300. Include brown rice."
        },
    )
    assert result.status_code == 200
    data = result.json()
    assert [i["product_id"] for i in data["cart"]["items"]] == ["milk_almarai_2l"]
    assert "Brown Rice 500g is unavailable" in data["reply"]
    assert "299.98" not in data["reply"]
    assert f"AED {data['cart']['total_aed']:.2f}" in data["reply"]
    assert data["substitution_offers"][0]["product_id"] == "rice_brown_500g"


def test_explicit_weekly_request_requires_nonempty_update_even_if_requested_item_is_unavailable(
    monkeypatch,
):
    import json

    import agents.google_runtime as runtime

    captured = []

    async def invoke(name, prompt, payload, schema):
        captured.append((payload, schema))
        return json.dumps(
            {
                "action": "update_cart",
                "reply": "Basket ready",
                "dietary": "halal",
                "budget": 300,
                "household": 4,
                "items": [{"product_id": "milk", "quantity": 2}],
                "requested_ids": ["brown"],
            }
        )

    monkeypatch.setattr(runtime, "invoke", invoke)
    inventory = [
        {
            "product_id": "brown",
            "product_name": "Brown Rice 500g",
            "category": "grains",
            "price_aed": 9.5,
            "stock_quantity": 0,
            "dietary_flags": "",
        },
        {
            "product_id": "milk",
            "product_name": "Milk 2L",
            "category": "dairy",
            "price_aed": 12,
            "stock_quantity": 20,
            "dietary_flags": "",
        },
    ]
    runtime.plan_shopping(
        "Weekly halal groceries, family of 4, AED 300. Include brown rice.",
        {},
        inventory,
    )
    payload, schema = captured[-1]
    assert payload["required_action"] == "update_cart"
    assert schema is runtime.WeeklyShoppingPlan
    with pytest.raises(ValueError):
        schema(
            action="clarify",
            reply="Ask?",
            dietary="halal",
            budget=300,
            household=4,
            items=[],
        )
    runtime.plan_shopping("What should weekly groceries include?", {}, inventory)
    assert captured[-1][1] is runtime.ShoppingPlan
