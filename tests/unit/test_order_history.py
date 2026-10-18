"""Order history reads the same durable records committed by checkout."""

from fastapi.testclient import TestClient


def test_confirmed_checkout_survives_reopen_and_customer_isolation(
    tmp_path, monkeypatch
):
    import tools.shared.alloydb_client as adapter
    from agents.aria.main import app

    path = tmp_path / "orders.sqlite"
    adapter._client = adapter.SqliteAlloyDBClient(str(path))
    client = TestClient(app)
    assert client.get("/aria/orders").json()["total"] == 0
    quote = client.post(
        "/aria/chat",
        json={
            "message": "review cart",
            "cart": [{"product_id": "milk_almarai_2l", "quantity": 1}],
        },
    ).json()
    request = {
        "message": "confirm",
        "session_id": quote["session_id"],
        "quote_id": quote["quote_id"],
        "cart": quote["cart"]["items"],
    }
    placed = client.post("/aria/chat", json=request)
    assert placed.status_code == 200
    order_id = placed.json()["order"]["order_id"]
    # An independent adapter reads from disk rather than the React receipt or
    # the adapter that handled checkout.
    adapter._client = adapter.SqliteAlloyDBClient(str(path))
    result = TestClient(app).get("/aria/orders").json()
    assert result["total"] == 1
    assert result["items"][0]["order_id"] == order_id
    assert result["items"][0]["items"][0]["product_name"] == "Almarai Full Fat Milk 2L"
    assert "idempotency_key" not in result["items"][0]
    assert client.get("/aria/orders?customer_id=ahmed_456").json()["items"] == []
    assert client.get("/aria/orders?store_id=jbr_01").json()["items"] == []
    assert client.get("/aria/orders?customer_id=missing").status_code == 404
    assert client.get("/aria/orders?page=0").status_code == 422
    duplicate = client.post("/aria/chat", json=request).json()
    assert duplicate["order"]["order_id"] == order_id
    assert client.get("/aria/orders").json()["total"] == 1
