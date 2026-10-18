#!/usr/bin/env python3
"""Fail-fast checks for the local application using Google infrastructure."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    from google.cloud import bigquery
    from sqlalchemy import text

    from tools.shared.database import get_engine
    from tools.shared.embeddings import get_embeddings
    from tools.shared.llm import get_llm
    from tools.shared.settings import settings

    if settings.use_mock:
        raise SystemExit("Google preflight requires USE_MOCK=false")
    with get_engine().connect() as conn:
        count, embedded = conn.execute(
            text("SELECT COUNT(*), COUNT(embedding) FROM inventory")
        ).one()
        if not count or count != embedded:
            raise SystemExit(
                "Catalog missing or embeddings incomplete; run scripts/init_gcp_db.py --seed --embed"
            )
        conn.execute(text("SELECT 1 FROM arc_records LIMIT 1"))
    client = bigquery.Client(
        project=settings.google_cloud_project, location=settings.bigquery_location
    )
    client.get_table(
        f"{settings.google_cloud_project}.{settings.bigquery_dataset}.incidents"
    )
    get_llm().generate(
        "Reply only with OK",
        max_output_tokens=32,
        thinking_config={"thinking_budget": 0},
    )
    get_embeddings().embed("brown rice")
    print(
        f"Google preflight passed: PostgreSQL catalog ({count} rows), BigQuery, Gemini, embeddings",
        flush=True,
    )


if __name__ == "__main__":
    main()
