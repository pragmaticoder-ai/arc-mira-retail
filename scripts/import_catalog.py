#!/usr/bin/env python3
"""Load sourced products into fictional MIRA stores; preserve import provenance."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text  # noqa: E402

from tools.shared.database import get_engine  # noqa: E402
from tools.shared.settings import settings  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STORE = "dubai_marina_01"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", type=Path, default=ROOT / "data/local/catalog/products.jsonl"
    )
    args = parser.parse_args()
    if settings.use_mock:
        parser.error("Real PostgreSQL required: USE_MOCK=false")
    records = {}
    for line in args.file.read_text().splitlines():
        row = json.loads(line)
        records[row["product_id"]] = row
    if not records:
        parser.error("No product records to import")
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(724031)"))
        sql = (ROOT / "data/schema/catalog_migration.sql").read_text()
        for stmt in sql.split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
        conn.execute(
            text("""INSERT INTO suppliers(supplier_id,supplier_name) VALUES
            ('mira_catalog','MIRA catalog') ON CONFLICT DO NOTHING""")
        )
    columns = [
        "product_id",
        "product_name",
        "category",
        "brand",
        "price_aed",
        "dietary_flags",
        "stock_quantity",
        "image_url",
        "images",
        "description",
        "attributes",
        "source_attributes",
        "retailer",
        "source_id",
        "source_sku",
        "source_url",
        "currency",
        "price_captured_at",
        "source_stock_quantity",
        "source_available",
        "inventory_origin",
        "unit_type",
        "source_category",
    ]
    json_columns = {"images", "attributes", "source_attributes"}
    values = [f"CAST(:{c} AS JSONB)" if c in json_columns else f":{c}" for c in columns]
    updates = [
        c + "=EXCLUDED." + c
        for c in columns
        if c not in {"product_id", "stock_quantity"}
    ]
    sql = f"""INSERT INTO inventory ({",".join(columns)}, store_id, aisle_ref, supplier_id)
        VALUES ({",".join(values)}, :store_id, 'Online', 'mira_catalog')
        ON CONFLICT(product_id,store_id) DO UPDATE SET {",".join(updates)}, updated_at=NOW()"""
    rows = []
    for record in records.values():
        row = {c: record.get(c) for c in columns}
        # Retailer provenance stays private. Own-label products belong to the
        # fictional MIRA demo; preserve the original record in source_attributes.
        row["product_id"] = "mira_" + str(record["source_id"])
        for key in ("product_name", "brand", "description", "source_category"):
            row[key] = re.sub(
                r"(?i)\b(?:lulu(?: hypermarket)?|carrefour)\b",
                "MIRA",
                row.get(key) or "",
            )
        row["attributes"] = {
            k: re.sub(r"(?i)\b(?:lulu(?: hypermarket)?|carrefour)\b", "MIRA", str(v))
            for k, v in (row["attributes"] or {}).items()
        }
        row["store_id"] = STORE
        row["inventory_origin"] = "demo_import"
        if record.get("source_stock_quantity") is None:
            row["stock_quantity"] = 20
        for c in json_columns:
            row[c] = json.dumps(row[c])
        rows.append(row)
    # Short batches do not lock out the live shopper for the entire import.
    for start in range(0, len(rows), 100):
        with engine.begin() as conn:
            conn.execute(text("SELECT pg_advisory_xact_lock(724031)"))
            head, rest = sql.split("VALUES ", 1)
            template, conflict = rest.split("ON CONFLICT", 1)
            bindings = {}
            groups = []
            for index, row in enumerate(rows[start : start + 100]):
                groups.append(
                    re.sub(r":([a-z_]+)\b", lambda m: f":{m[1]}_{index}", template)
                )
                bindings.update({f"{key}_{index}": value for key, value in row.items()})
            conn.execute(
                text(head + "VALUES " + ",".join(groups) + " ON CONFLICT " + conflict),
                bindings,
            )
        print(f"Imported {min(start + 100, len(rows))}/{len(rows)}", flush=True)
    counts = Counter(r["category"] for r in records.values())
    print(
        json.dumps(
            {
                "store_id": STORE,
                "distinct_products": len(records),
                "categories": dict(counts),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
