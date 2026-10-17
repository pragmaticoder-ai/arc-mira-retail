"""AlloyDB (PostgreSQL) adapter — placeholder with in-memory mock.

Operational data: customer_profiles, inventory, orders, promotions,
replenishment_schedule, purchase_orders. Tools call these methods, never raw
SQL or pg8000 directly, so mock swaps to real with one env flag.

Mock backs reads with tools/shared/mock_inventory.py and keeps writes
(orders, purchase_orders, discount flags) in process memory for the session.
Real impl (TODO) uses the AlloyDB connector + pg8000 per DEPLOYMENT.md.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

from tools.shared.settings import settings


class AlloyDBClient(ABC):
    @abstractmethod
    def get_customer(self, customer_id: str) -> dict | None: ...

    @abstractmethod
    def list_inventory(self, store_id: str, *, category: str | None = None) -> list[dict]: ...

    @abstractmethod
    def get_product(self, product_id: str) -> dict | None: ...

    @abstractmethod
    def list_active_promotions(self, store_id: str) -> list[dict]: ...

    @abstractmethod
    def insert_order(self, order: dict) -> dict: ...

    @abstractmethod
    def insert_purchase_order(self, po: dict) -> dict: ...

    @abstractmethod
    def set_discount_active(self, product_id: str, active: bool) -> None: ...


class MockAlloyDBClient(AlloyDBClient):
    def __init__(self) -> None:
        from tools.shared import mock_inventory

        # Copy so in-session writes don't mutate the module constants.
        self._customers = {c["customer_id"]: dict(c) for c in mock_inventory.MOCK_CUSTOMERS}
        self._inventory = {p["product_id"]: dict(p) for p in mock_inventory.MOCK_INVENTORY}
        self._promotions = [dict(p) for p in mock_inventory.MOCK_PROMOTIONS]
        self._orders: dict[str, dict] = {}
        self._purchase_orders: dict[str, dict] = {}

    def get_customer(self, customer_id: str) -> dict | None:
        return self._customers.get(customer_id)

    def list_inventory(self, store_id: str, *, category: str | None = None) -> list[dict]:
        out = [p for p in self._inventory.values() if p["store_id"] == store_id]
        if category:
            out = [p for p in out if p["category"] == category]
        return out

    def get_product(self, product_id: str) -> dict | None:
        return self._inventory.get(product_id)

    def list_active_promotions(self, store_id: str) -> list[dict]:
        return [p for p in self._promotions if p.get("is_active")]

    def insert_order(self, order: dict) -> dict:
        order_id = order.get("order_id") or f"ORD-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:4]}"
        start = datetime.now() + timedelta(hours=6)
        end = start + timedelta(hours=2)
        record = {
            **order,
            "order_id": order_id,
            "status": "confirmed",
            "estimated_delivery_window": f"{start:%H:%M}–{end:%H:%M}",
            "created_at": datetime.now().isoformat(),
        }
        self._orders[order_id] = record
        return record

    def insert_purchase_order(self, po: dict) -> dict:
        po_id = po.get("po_id") or f"po_{uuid.uuid4().hex[:8]}"
        record = {**po, "po_id": po_id, "status": "pending", "created_at": datetime.now().isoformat()}
        self._purchase_orders[po_id] = record
        return record

    def set_discount_active(self, product_id: str, active: bool) -> None:
        if product_id in self._inventory:
            self._inventory[product_id]["discount_active"] = active


class RealAlloyDBClient(AlloyDBClient):
    """TODO(backend): implement with google.cloud.alloydb.connector + pg8000.
    Connection details come from settings (Secret Manager in production)."""

    def __init__(self) -> None:
        raise NotImplementedError(
            "RealAlloyDBClient not implemented. Set USE_MOCK=true or wire AlloyDB "
            f"(host={settings.alloydb_host})."
        )

    def get_customer(self, customer_id: str) -> dict | None: ...
    def list_inventory(self, store_id: str, *, category: str | None = None) -> list[dict]: ...
    def get_product(self, product_id: str) -> dict | None: ...
    def list_active_promotions(self, store_id: str) -> list[dict]: ...
    def insert_order(self, order: dict) -> dict: ...
    def insert_purchase_order(self, po: dict) -> dict: ...
    def set_discount_active(self, product_id: str, active: bool) -> None: ...


# Single shared instance so in-session mock writes persist across tool calls.
_client: AlloyDBClient | None = None


def get_alloydb() -> AlloyDBClient:
    global _client
    if _client is None:
        _client = MockAlloyDBClient() if settings.use_mock else RealAlloyDBClient()
    return _client
