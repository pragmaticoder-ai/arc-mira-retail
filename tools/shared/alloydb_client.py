"""Retail persistence interface and explicit offline test adapters.

Google mode uses PostgresClient. In-memory and SQLite adapters are available
only when offline mode is explicitly selected.
"""

from __future__ import annotations

import copy
import json
import sqlite3
import threading
import uuid
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any

from tools.shared.clock import now, today
from tools.shared.settings import settings


class AlloyDBClient(ABC):
    def list_stores(self) -> list[dict]:
        raise NotImplementedError

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
    def set_discount_active(self, product_id: str, active: bool, store_id: str | None = None, discount_pct: float | None = None) -> None: ...

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


    def transaction(self) -> AbstractContextManager[Any]:
        raise NotImplementedError

    def get_session(self, session_id: str) -> dict | None:
        raise NotImplementedError

    def save_session(self, session_id: str, state: dict) -> None:
        raise NotImplementedError

    def find_order(self, key: str, *, max_age_seconds: int | None = None) -> dict | None:
        raise NotImplementedError

    def decide_purchase_order(self, po_id: str, status: str) -> dict:
        raise NotImplementedError

    def save_decision(self, key: str, decision: dict) -> dict:
        raise NotImplementedError

    def get_decision(self, key: str) -> dict | None:
        raise NotImplementedError

    def list_decisions(self, store_id: str) -> list[dict]:
        raise NotImplementedError

    def transfer_stock(self, product_id: str, source: str, destination: str, quantity: int) -> None:
        raise NotImplementedError


def state_operation(fn):
    """Serialize local reads and writes, including nested checkout operations."""
    @wraps(fn)
    def wrapped(self, *args, **kwargs):
        with self.transaction():
            return copy.deepcopy(fn(self, *args, **kwargs))
    return wrapped


class RetailStateClient(AlloyDBClient):
    """Shared business operations over a transaction-scoped retail state."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._depth = 0
        self._sessions: dict[str, dict] = {}
        self._decisions: dict[str, dict] = {}
        self._customers: dict[str, dict] = {}
        self._inventory: dict[tuple[str, str], dict] = {}
        self._promotions: list[dict] = []
        self._replenishment: dict[tuple[str, str], dict] = {}
        self._orders: dict[str, dict] = {}
        self._purchase_orders: dict[str, dict] = {}
        self._stores: list[dict] = []
        self._primary_store = "dubai_marina_01"

    def list_stores(self) -> list[dict]:
        return self._stores

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
            if quantity <= 0 or row["stock_quantity"] < quantity:
                raise ValueError("Invalid quantity or insufficient stock")
            row["stock_quantity"] -= quantity

    def list_active_promotions(self, store_id: str) -> list[dict]:
        return [p for p in self._promotions if p.get("is_active")]

    def increment_promotion_usage(self, promotion_id: str) -> int:
        for p in self._promotions:
            if p["promotion_id"] == promotion_id:
                p["times_applied"] = int(p.get("times_applied", 0)) + 1
                return p["times_applied"]
        return 0

    def insert_order(self, order: dict) -> dict:
        current = now()
        order_id = order.get("order_id") or f"MR-{current:%Y}-{uuid.uuid4().hex[:4].upper()}"
        # Next available 2-hour slot tomorrow morning (always a future window).
        start = (current + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=2)
        record = {
            **order,
            "order_id": order_id,
            "status": "confirmed",
            "estimated_delivery_window": f"{start:%a %d %b · %H:%M}–{end:%H:%M}",
            "delivery_start_iso": start.isoformat(),
            "created_at": current.isoformat(),
        }
        self._orders[order_id] = record
        return record

    def insert_purchase_order(self, po: dict) -> dict:
        current = now()
        # Idempotency: reuse a pending PO for the same product+store within 24h.
        for existing in self._purchase_orders.values():
            if (
                existing["product_id"] == po["product_id"]
                and existing["store_id"] == po["store_id"]
                and existing["status"] in {"pending", "approved", "rejected"}
            ):
                try:
                    age = current - datetime.fromisoformat(existing["created_at"])
                    if age <= timedelta(hours=24):
                        return existing
                except (ValueError, KeyError):
                    pass
        seq = len(self._purchase_orders) + 1
        po_id = po.get("po_id") or f"PO-{current:%Y}-{seq:04d}"
        record = {
            **po,
            "po_id": po_id,
            "status": "pending",
            "created_by": "PULSE",
            "created_at": current.isoformat(),
        }
        self._purchase_orders[po_id] = record
        return record

    def set_discount_active(self, product_id: str, active: bool, store_id: str | None = None,
                            discount_pct: float | None = None) -> None:
        for (pid, sid), row in self._inventory.items():
            if pid == product_id and (store_id is None or sid == store_id):
                row["discount_active"] = active
                if discount_pct is not None:
                    row["discount_pct"] = discount_pct
                    row["discounted_price_aed"] = round(row["price_aed"] * (1 - discount_pct / 100), 2)

    def get_replenishment(self, store_id: str, product_id: str) -> dict | None:
        return self._replenishment.get((store_id, product_id))


    @contextmanager
    def transaction(self):
        with self._lock:
            snapshot = self._dump() if self._depth == 0 else None
            self._depth += 1
            try:
                yield self
            except Exception:
                if snapshot is not None:
                    self._load(snapshot)
                raise
            finally:
                self._depth -= 1

    def _dump(self) -> dict:
        return copy.deepcopy({
            "inventory": list(self._inventory.values()), "customers": self._customers,
            "promotions": self._promotions, "orders": self._orders,
            "purchase_orders": self._purchase_orders, "sessions": self._sessions,
            "decisions": self._decisions,
        })

    def _load(self, state: dict) -> None:
        self._inventory = {(p["product_id"], p["store_id"]): p for p in state["inventory"]}
        for name in ("customers", "promotions", "orders", "purchase_orders", "sessions", "decisions"):
            setattr(self, "_" + name, state.get(name, {}))

    def get_session(self, session_id: str) -> dict | None:
        return self._sessions.get(session_id)

    def save_session(self, session_id: str, state: dict) -> None:
        self._sessions[session_id] = copy.deepcopy(state)

    def find_order(self, key: str, *, max_age_seconds: int | None = None) -> dict | None:
        for order in self._orders.values():
            if order.get("idempotency_key") == key:
                age = (now() - datetime.fromisoformat(order["created_at"])).total_seconds()
                if max_age_seconds is None or age <= max_age_seconds:
                    return order
        return None

    def decide_purchase_order(self, po_id: str, status: str) -> dict:
        if status not in {"approved", "rejected"}:
            raise ValueError("Invalid decision")
        po = self._purchase_orders.get(po_id)
        if po is None:
            raise ValueError("Purchase order not found")
        if po["status"] != "pending" and po["status"] != status:
            raise ValueError("Purchase order already decided")
        po.update(status=status, decided_at=now().isoformat())
        return po

    def save_decision(self, key: str, decision: dict) -> dict:
        existing = self._decisions.get(key)
        if existing and existing.get("status") != decision.get("status"):
            raise ValueError("This proposal already has a decision")
        self._decisions[key] = existing or {**decision, "decided_at": now().isoformat()}
        return self._decisions[key]

    def get_decision(self, key: str) -> dict | None:
        return self._decisions.get(key)

    def list_decisions(self, store_id: str) -> list[dict]:
        return [d for d in self._decisions.values() if d.get("store_id") == store_id]

    def list_orders(self, customer_id: str, store_id: str | None = None) -> list[dict]:
        return sorted([o for o in self._orders.values() if o.get("customer_id") == customer_id
            and (store_id is None or o.get("store_id") == store_id)],
            key=lambda o: (o.get("created_at", ""), o["order_id"]), reverse=True)

    def transfer_stock(self, product_id: str, source: str, destination: str, quantity: int) -> None:
        src = self._inventory.get((product_id, source))
        dst = self._inventory.get((product_id, destination))
        if not src or not dst or quantity <= 0 or src["stock_quantity"] - quantity < src["reorder_threshold"]:
            raise ValueError("Transfer would breach source safety stock")
        src["stock_quantity"] -= quantity
        dst["stock_quantity"] += quantity


# Every public operation participates in the same transaction. Deep copies
# prevent callers from mutating persisted state outside that transaction.
for _name, _method in list(vars(RetailStateClient).items()):
    if callable(_method) and not _name.startswith("_") and _name != "transaction":
        setattr(RetailStateClient, _name, state_operation(_method))


class MockAlloyDBClient(RetailStateClient):
    def __init__(self) -> None:
        from tools.shared import mock_inventory

        # Copy so in-session writes don't mutate the module constants.
        self._lock = threading.RLock()
        self._depth = 0
        self._sessions: dict[str, dict] = {}
        self._decisions: dict[str, dict] = {}
        self._customers: dict[str, dict] = {c["customer_id"]: dict(c) for c in mock_inventory.MOCK_CUSTOMERS}
        # Inventory is store-aware: keyed by (product_id, store_id).
        self._inventory: dict[tuple[str, str], dict] = {
            (p["product_id"], p["store_id"]): dict(p) for p in mock_inventory.MOCK_INVENTORY
        }
        # Keep perishable seed ages stable while business time moves forward.
        for row in self._inventory.values():
            if row.get("expiry_date"):
                from datetime import date
                offset = date.fromisoformat(row["expiry_date"]) - date(2026, 10, 17)
                row["expiry_date"] = (today() + offset).isoformat()
            row.setdefault("supplier_id", "demo_supplier")
        self._stores = copy.deepcopy(mock_inventory.MOCK_STORES)
        self._primary_store = mock_inventory.STORE_ID
        self._promotions: list[dict] = [dict(p) for p in mock_inventory.MOCK_PROMOTIONS]
        self._replenishment: dict[tuple[str, str], dict] = {
            (r["store_id"], r["product_id"]): dict(r)
            for r in getattr(mock_inventory, "MOCK_REPLENISHMENT", [])
        }
        self._orders: dict[str, dict] = {}
        self._purchase_orders: dict[str, dict] = {}



class SqliteAlloyDBClient(MockAlloyDBClient):
    """Durable local adapter. SQLite's write lock makes checkout atomic across
    processes. This is for a single-host prototype, not a cloud database."""

    def __init__(self, db_path: str) -> None:
        super().__init__()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, isolation_level=None, check_same_thread=False, timeout=15)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("CREATE TABLE IF NOT EXISTS arc_state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)")
        self._conn.execute("INSERT OR IGNORE INTO arc_state VALUES (1, ?)", (json.dumps(self._dump()),))

    @contextmanager
    def transaction(self):
        with self._lock:
            outer = self._depth == 0
            if outer:
                self._conn.execute("BEGIN IMMEDIATE")
                self._load(json.loads(self._conn.execute("SELECT payload FROM arc_state WHERE id=1").fetchone()[0]))
            self._depth += 1
            try:
                yield self
                if outer:
                    self._conn.execute("UPDATE arc_state SET payload=? WHERE id=1", (json.dumps(self._dump()),))
                    self._conn.execute("COMMIT")
            except Exception:
                if outer:
                    self._conn.execute("ROLLBACK")
                    self._load(json.loads(self._conn.execute("SELECT payload FROM arc_state WHERE id=1").fetchone()[0]))
                raise
            finally:
                self._depth -= 1


# Single shared instance so in-session mock writes persist across tool calls.
_client: AlloyDBClient | None = None


def get_alloydb() -> AlloyDBClient:
    global _client
    if _client is None:
        if not settings.use_mock:
            from tools.shared.postgres_client import PostgresClient

            _client = PostgresClient()
        elif settings.arc_state_db:
            _client = SqliteAlloyDBClient(settings.arc_state_db)
        else:
            _client = MockAlloyDBClient()
    return _client
