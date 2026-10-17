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

    @abstractmethod
    def get_replenishment(self, store_id: str, product_id: str) -> dict | None: ...

    @abstractmethod
    def increment_promotion_usage(self, promotion_id: str) -> int:
        """Increment and return promotions.times_applied for a promotion."""

    @abstractmethod
    def get_product_at_store(self, product_id: str, store_id: str) -> dict | None:
        """The inventory row for a product at a specific store (store-aware)."""

    @abstractmethod
    def list_product_across_stores(self, product_id: str, *, exclude_store_id: str | None = None) -> list[dict]:
        """All store rows for a product, for check_stock alternatives."""

    @abstractmethod
    def decrement_stock(self, product_id: str, store_id: str, quantity: int) -> None:
        """Reduce stock for a product at a store (place_order)."""


class MockAlloyDBClient(AlloyDBClient):
    def __init__(self) -> None:
        from tools.shared import mock_inventory

        # Copy so in-session writes don't mutate the module constants.
        self._customers = {c["customer_id"]: dict(c) for c in mock_inventory.MOCK_CUSTOMERS}
        # Inventory is store-aware: keyed by (product_id, store_id).
        self._inventory = {
            (p["product_id"], p["store_id"]): dict(p) for p in mock_inventory.MOCK_INVENTORY
        }
        self._primary_store = mock_inventory.STORE_ID
        self._promotions = [dict(p) for p in mock_inventory.MOCK_PROMOTIONS]
        self._replenishment = {
            (r["store_id"], r["product_id"]): dict(r)
            for r in getattr(mock_inventory, "MOCK_REPLENISHMENT", [])
        }
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
        # Default to the primary store for backward compatibility.
        row = self._inventory.get((product_id, self._primary_store))
        if row:
            return row
        # Fall back to any store that stocks it.
        for (pid, _sid), p in self._inventory.items():
            if pid == product_id:
                return p
        return None

    def get_product_at_store(self, product_id: str, store_id: str) -> dict | None:
        return self._inventory.get((product_id, store_id))

    def list_product_across_stores(self, product_id: str, *, exclude_store_id: str | None = None) -> list[dict]:
        rows = [p for (pid, _sid), p in self._inventory.items() if pid == product_id]
        if exclude_store_id:
            rows = [p for p in rows if p["store_id"] != exclude_store_id]
        return rows

    def decrement_stock(self, product_id: str, store_id: str, quantity: int) -> None:
        row = self._inventory.get((product_id, store_id))
        if row:
            row["stock_quantity"] = max(0, row["stock_quantity"] - quantity)

    def list_active_promotions(self, store_id: str) -> list[dict]:
        return [p for p in self._promotions if p.get("is_active")]

    def increment_promotion_usage(self, promotion_id: str) -> int:
        for p in self._promotions:
            if p["promotion_id"] == promotion_id:
                p["times_applied"] = int(p.get("times_applied", 0)) + 1
                return p["times_applied"]
        return 0

    def insert_order(self, order: dict) -> dict:
        now = datetime.now()
        order_id = order.get("order_id") or f"MR-{now:%Y}-{uuid.uuid4().hex[:4].upper()}"
        # Next available 2-hour slot tomorrow morning (always a future window).
        start = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=2)
        record = {
            **order,
            "order_id": order_id,
            "status": "confirmed",
            "estimated_delivery_window": f"{start:%a %d %b · %H:%M}–{end:%H:%M}",
            "delivery_start_iso": start.isoformat(),
            "created_at": now.isoformat(),
        }
        self._orders[order_id] = record
        return record

    def insert_purchase_order(self, po: dict) -> dict:
        now = datetime.now()
        # Idempotency: reuse a pending PO for the same product+store within 24h.
        for existing in self._purchase_orders.values():
            if (
                existing["product_id"] == po["product_id"]
                and existing["store_id"] == po["store_id"]
                and existing["status"] == "pending"
            ):
                try:
                    age = now - datetime.fromisoformat(existing["created_at"])
                    if age <= timedelta(hours=24):
                        return existing
                except (ValueError, KeyError):
                    pass
        seq = len(self._purchase_orders) + 1
        po_id = po.get("po_id") or f"PO-{now:%Y}-{seq:04d}"
        record = {
            **po,
            "po_id": po_id,
            "status": "pending",
            "created_by": "PULSE",
            "created_at": now.isoformat(),
        }
        self._purchase_orders[po_id] = record
        return record

    def set_discount_active(self, product_id: str, active: bool) -> None:
        # Apply across all stores that stock the product.
        for (pid, _sid), row in self._inventory.items():
            if pid == product_id:
                row["discount_active"] = active

    def get_replenishment(self, store_id: str, product_id: str) -> dict | None:
        return self._replenishment.get((store_id, product_id))


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
    def get_replenishment(self, store_id: str, product_id: str) -> dict | None: ...
    def increment_promotion_usage(self, promotion_id: str) -> int: ...
    def get_product_at_store(self, product_id: str, store_id: str) -> dict | None: ...
    def list_product_across_stores(self, product_id: str, *, exclude_store_id: str | None = None) -> list[dict]: ...
    def decrement_stock(self, product_id: str, store_id: str, quantity: int) -> None: ...


# Single shared instance so in-session mock writes persist across tool calls.
_client: AlloyDBClient | None = None


def get_alloydb() -> AlloyDBClient:
    global _client
    if _client is None:
        _client = MockAlloyDBClient() if settings.use_mock else RealAlloyDBClient()
    return _client
