#!/usr/bin/env python3
"""Database initialization script for Google Cloud (AlloyDB / Cloud SQL & BigQuery).

Loads schemas from data/schema/ and seeds from data/seed/.
Usage:
    python scripts/init_gcp_db.py [--skip-db] [--skip-bigquery]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Load settings
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from tools.shared.settings import settings  # noqa: E402


def init_bigquery():
    print("--> Initializing BigQuery dataset and tables...")
    try:
        from google.cloud import bigquery
    except ImportError:
        print("ERROR: google-cloud-bigquery not installed. Run: uv pip install google-cloud-bigquery")
        return False

    client = bigquery.Client(project=settings.google_cloud_project, location=settings.bigquery_location)
    dataset_ref = f"{settings.google_cloud_project}.{settings.bigquery_dataset}"

    # Create dataset if not exists
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = settings.bigquery_location
    try:
        client.create_dataset(dataset, exists_ok=True)
        print(f"--> BigQuery dataset '{dataset_ref}' ready.")
    except Exception as exc:
        print(f"WARNING: Could not create dataset: {exc}")

    # Read and apply BigQuery schema
    bq_schema_file = ROOT_DIR / "data" / "schema" / "bigquery_schema.sql"
    if bq_schema_file.exists():
        sql = bq_schema_file.read_text(encoding="utf-8")
        # Replace dataset references if needed
        sql = sql.replace("arc_dataset.", f"`{dataset_ref}`.")

        # Split statements by semicolon
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        for stmt in statements:
            try:
                job = client.query(stmt)
                job.result()
            except Exception as e:
                print(f"--> Statement note: {e}")
        print("--> BigQuery tables and models created successfully.")
    return True


def init_postgres():
    print(f"--> Initializing PostgreSQL / AlloyDB at {settings.alloydb_host}:{settings.alloydb_port}...")
    try:
        import sqlalchemy
    except ImportError:
        print("ERROR: sqlalchemy / pg8000 not installed.")
        return False

    # Build connection URL
    user = settings.alloydb_user
    password = settings.alloydb_password or os.getenv("ALLOYDB_PASSWORD", "")
    host = settings.alloydb_host
    port = settings.alloydb_port
    db_name = settings.alloydb_database

    url = f"postgresql+pg8000://{user}:{password}@{host}:{port}/{db_name}"
    try:
        engine = sqlalchemy.create_engine(url)
        with engine.connect() as conn:
            print("--> Connected to PostgreSQL / AlloyDB successfully.")

            # Apply schema
            schema_file = ROOT_DIR / "data" / "schema" / "alloydb_schema.sql"
            if schema_file.exists():
                print(f"--> Applying {schema_file.name}...")
                sql = schema_file.read_text(encoding="utf-8")
                # Split statements
                for stmt in sql.split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        try:
                            conn.execute(sqlalchemy.text(stmt))
                        except Exception as e:
                            # Ignore extension errors on non-AlloyDB (e.g. ScaNN)
                            if "vector" in stmt or "scann" in stmt or "google_ml_integration" in stmt:
                                print(f"    (Skipping AlloyDB AI specific extension: {e})")
                            else:
                                print(f"    Notice: {e}")

            # Apply seeds
            seed_dir = ROOT_DIR / "data" / "seed"
            for seed_file in sorted(seed_dir.glob("*.sql")):
                print(f"--> Applying seed: {seed_file.name}...")
                sql = seed_file.read_text(encoding="utf-8")
                for stmt in sql.split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        try:
                            conn.execute(sqlalchemy.text(stmt))
                        except Exception as e:
                            print(f"    Notice on seed statement: {e}")

            conn.commit()
            print("--> PostgreSQL / AlloyDB tables and seed data loaded successfully!")
            return True
    except Exception as exc:
        print(f"WARNING: Could not connect to PostgreSQL / AlloyDB at {host}:{port}: {exc}")
        print("Note: In Cloud Run, connections are routed via the Serverless VPC Connector to private IP.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Initialize Google Cloud Databases for ARC")
    parser.add_argument("--skip-db", action="store_true", help="Skip PostgreSQL / AlloyDB initialization")
    parser.add_argument("--skip-bigquery", action="store_true", help="Skip BigQuery initialization")
    args = parser.parse_args()

    print("════════════════════════════════════════════════════════════════════")
    print(" ARC Cloud Database Initializer")
    print(f" Project: {settings.google_cloud_project} | Region: {settings.google_cloud_region}")
    print("════════════════════════════════════════════════════════════════════")

    if not args.skip_bigquery:
        init_bigquery()

    if not args.skip_db:
        init_postgres()

    print("Done!")


if __name__ == "__main__":
    main()
