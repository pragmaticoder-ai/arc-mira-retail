#!/usr/bin/env python3
"""Apply idempotent schemas; optionally load sample catalog and Google embeddings.

No synthetic shopping incidents or model forecasts are generated.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from tools.shared.settings import settings  # noqa: E402


def statements(path: Path):
    # These repository SQL files contain no procedural blocks or quoted semicolons.
    sql = re.sub(r"--[^\n]*", "", path.read_text())
    return [stmt.strip() for stmt in sql.split(";") if stmt.strip()]


def init_postgres(seed: bool = False):
    from sqlalchemy import text

    from tools.shared.database import get_engine

    with get_engine().begin() as conn:
        for stmt in statements(ROOT_DIR / "data/schema/alloydb_schema.sql"):
            conn.execute(text(stmt))
        for stmt in statements(ROOT_DIR / "data/schema/catalog_migration.sql"):
            conn.execute(text(stmt))
        if seed:
            for path in sorted((ROOT_DIR / "data/seed").glob("*.sql")):
                for stmt in statements(path):
                    # Existing inventory, prices and decisions must survive reruns.
                    conn.execute(text(stmt.rstrip() + " ON CONFLICT DO NOTHING"))
    print(
        "PostgreSQL schema ready" + ("; sample catalog loaded" if seed else ""),
        flush=True,
    )


def init_bigquery():
    from google.cloud import bigquery

    client = bigquery.Client(
        project=settings.google_cloud_project, location=settings.bigquery_location
    )
    dataset_ref = f"{settings.google_cloud_project}.{settings.bigquery_dataset}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = settings.bigquery_location
    client.create_dataset(dataset, exists_ok=True)
    for stmt in statements(ROOT_DIR / "data/schema/bigquery_schema.sql"):
        # Training requires real history and is deliberately a separate task.
        if re.search(r"CREATE\s+OR\s+REPLACE\s+MODEL", stmt, re.I):
            continue
        qualified = re.sub(
            r"arc_dataset\.(\w+)", lambda m: f"`{dataset_ref}.{m[1]}`", stmt
        )
        client.query(qualified).result()
    print(
        "BigQuery tables ready (forecast training skipped until real history exists)",
        flush=True,
    )


def embed_catalog():
    from sqlalchemy import text

    from tools.shared.database import get_engine
    from tools.shared.embeddings import RealEmbeddings, product_document

    if settings.embedding_dim != 768:
        raise ValueError("Current SQL schema requires EMBEDDING_DIM=768")
    engine = get_engine()
    with engine.connect() as conn:
        rows = list(
            conn.execute(
                text("SELECT * FROM inventory WHERE embedding IS NULL")
            ).mappings()
        )
    embedder = RealEmbeddings()
    vectors = {}
    for row in rows:
        document = product_document(dict(row))
        if document not in vectors:
            vectors[document] = embedder.embed(document)
        vector = vectors[document]
        with engine.begin() as conn:
            conn.execute(
                text("""UPDATE inventory SET embedding=CAST(:embedding AS vector)
                WHERE product_id=:pid AND store_id=:store AND embedding IS NULL"""),
                {
                    "embedding": str(vector),
                    "pid": row["product_id"],
                    "store": row["store_id"],
                },
            )
    print(f"Google embeddings stored for {len(rows)} catalog rows", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-db", action="store_true")
    parser.add_argument("--skip-bigquery", action="store_true")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Explicitly load the sample store/product/customer catalog",
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Generate missing catalog embeddings using Google",
    )
    args = parser.parse_args()
    if settings.use_mock:
        parser.error(
            "Set USE_MOCK=false; this script initializes real Google resources"
        )
    if not args.skip_db:
        init_postgres(args.seed)
    if not args.skip_bigquery:
        init_bigquery()
    if args.embed:
        embed_catalog()


if __name__ == "__main__":
    main()
