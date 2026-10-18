"""PostgreSQL retail adapter: SQL catalog/inventory and one JSONB row per entity.

A transaction advisory lock serializes checkout and manager decisions across local
processes. This intentionally favors correctness over throughput for the demo.
No mock data is imported or generated; initialization is an explicit script.
"""

from __future__ import annotations

import copy
import json
from contextlib import contextmanager
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import text

from tools.shared.alloydb_client import RetailStateClient, state_operation
from tools.shared.database import get_engine


def _value(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime, time)):
        return v.isoformat()
    return v


INVENTORY_COLUMNS = "product_id,product_name,category,brand,price_aed,dietary_flags,store_id,aisle_ref,stock_quantity,reorder_threshold,supplier_id,is_perishable,expiry_date,discount_active,discount_pct,attributes,source_attributes->>'ingredients' AS ingredients"


class PostgresClient(RetailStateClient):
    def __init__(self):
        super().__init__()
        self._engine = get_engine()

    def _inventory_rows(self, where, params):
        rows = self._active_conn.execute(
            text(f"SELECT {INVENTORY_COLUMNS} FROM inventory WHERE {where}"), params
        ).mappings()
        for raw in rows:
            row = {k: _value(v) for k, v in raw.items()}
            key = (row["product_id"], row["store_id"])
            if key not in self._inventory:
                row["discounted_price_aed"] = round(
                    row["price_aed"] * (1 - (row.get("discount_pct") or 0) / 100), 2
                )
                self._inventory[key] = row
                self._original_inventory[key] = copy.deepcopy(row)

    @state_operation
    def list_inventory(self, store_id, *, category=None):
        self._inventory_rows(
            "store_id=:store" + (" AND category=:category" if category else ""),
            {"store": store_id, "category": category},
        )
        return super().list_inventory(store_id, category=category)

    @state_operation
    def get_product(self, product_id):
        self._inventory_rows("product_id=:pid", {"pid": product_id})
        return super().get_product(product_id)

    @state_operation
    def get_product_at_store(self, product_id, store_id):
        self._inventory_rows(
            "product_id=:pid AND store_id=:store",
            {"pid": product_id, "store": store_id},
        )
        return super().get_product_at_store(product_id, store_id)

    @state_operation
    def list_product_across_stores(self, product_id, *, exclude_store_id=None):
        self._inventory_rows("product_id=:pid", {"pid": product_id})
        return super().list_product_across_stores(
            product_id, exclude_store_id=exclude_store_id
        )

    @state_operation
    def decrement_stock(self, product_id, store_id, quantity):
        self.get_product_at_store(product_id, store_id)
        return super().decrement_stock(product_id, store_id, quantity)

    @state_operation
    def set_discount_active(self, product_id, active, store_id=None, discount_pct=None):
        self._inventory_rows("product_id=:pid", {"pid": product_id})
        return super().set_discount_active(product_id, active, store_id, discount_pct)

    @state_operation
    def transfer_stock(self, product_id, source, destination, quantity):
        self._inventory_rows("product_id=:pid", {"pid": product_id})
        return super().transfer_stock(product_id, source, destination, quantity)

    def _rows(self, conn, table):
        # Table names are internal constants, never user input.
        return [
            {k: _value(v) for k, v in row.items()}
            for row in conn.execute(text(f"SELECT * FROM {table}")).mappings()
        ]

    def _read(self, conn):
        self._stores = [row for row in self._rows(conn, "stores") if row["is_active"]]
        self._inventory = {}
        self._original_inventory = {}
        self._customers = {
            r["customer_id"]: r for r in self._rows(conn, "customer_profiles")
        }
        self._promotions = self._rows(conn, "promotions")
        for row in self._promotions:
            for key in ("valid_from", "valid_until"):
                if row.get(key):
                    row[key] = row[key][:10]
        self._replenishment = {
            (r["store_id"], r["product_id"]): r
            for r in self._rows(conn, "replenishment_schedule")
        }
        for entity in ("sessions", "decisions", "orders", "purchase_orders"):
            setattr(self, "_" + entity, {})
        for row in conn.execute(
            text("SELECT entity, key, payload FROM arc_records")
        ).mappings():
            getattr(self, "_" + row["entity"])[row["key"]] = row["payload"]

        for customer_id, customer in self._customers.items():
            orders = sorted(
                [
                    o
                    for o in self._orders.values()
                    if o.get("customer_id") == customer_id
                ],
                key=lambda o: o.get("created_at", ""),
                reverse=True,
            )
            recent = {}
            for order in orders:
                for item in order.get("items", []):
                    recent.setdefault(
                        item["product_id"],
                        {
                            "product_id": item["product_id"],
                            "product_name": item["product_name"],
                            "last_ordered": order["created_at"][:10],
                        },
                    )
            customer["last_orders"] = list(recent.values())[:3]

    def _write(self, conn, previous):
        old_inventory = self._original_inventory
        for key, row in self._inventory.items():
            if row != old_inventory.get(key):
                conn.execute(
                    text("""UPDATE inventory SET stock_quantity=:stock_quantity,
                    discount_active=:discount_active, discount_pct=:discount_pct, updated_at=NOW()
                    WHERE product_id=:product_id AND store_id=:store_id"""),
                    row,
                )
        old_promos = {r["promotion_id"]: r for r in previous["promotions"]}
        for row in self._promotions:
            if row != old_promos.get(row["promotion_id"]):
                conn.execute(
                    text(
                        "UPDATE promotions SET times_applied=:times_applied WHERE promotion_id=:promotion_id"
                    ),
                    row,
                )
        for entity in ("sessions", "decisions", "orders", "purchase_orders"):
            for key, payload in getattr(self, "_" + entity).items():
                if payload != previous[entity].get(key):
                    conn.execute(
                        text("""INSERT INTO arc_records(entity, key, payload)
                        VALUES (:entity, :key, CAST(:payload AS JSONB))
                        ON CONFLICT(entity, key) DO UPDATE SET payload=EXCLUDED.payload"""),
                        {"entity": entity, "key": key, "payload": json.dumps(payload)},
                    )

    @contextmanager
    def transaction(self):
        with self._lock:
            if self._depth:
                self._depth += 1
                try:
                    yield self
                finally:
                    self._depth -= 1
                return
            with self._engine.begin() as conn:
                conn.execute(text("SELECT pg_advisory_xact_lock(724031)"))
                self._active_conn = conn
                self._read(conn)
                previous = self._dump()
                self._depth = 1
                try:
                    yield self
                    self._write(conn, previous)
                except BaseException:
                    self._load(previous)
                    raise
                finally:
                    self._depth = 0
                    self._active_conn = None
