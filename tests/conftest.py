"""Shared pytest fixtures for ARC backend tests.

Provides:
- PostgreSQL container (AlloyDB-compatible) for integration tests
- BigQuery emulator container for bridge tests
- Mock clients for unit tests
"""

from __future__ import annotations

import os
import time

import pytest
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer
from testcontainers.core.container import DockerContainer


# ── PostgreSQL container (AlloyDB-compatible) ─────────────────────────────

@pytest.fixture(scope="session")
def postgres_container():
    """
    Spins up a PostgreSQL 15 container for the test session.
    AlloyDB is PostgreSQL-compatible — all schema/queries work identically.
    """
    with PostgresContainer(
        image="postgres:15",
        username="arc_test",
        password="arc_test_password",
        dbname="arc_test_db",
        driver="pg8000"
    ) as postgres:
        yield postgres


@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """SQLAlchemy engine connected to the test PostgreSQL container."""
    engine = create_engine(postgres_container.get_connection_url())
    # Run schema migrations
    schema_path = "data/schema/alloydb_schema.sql"
    if os.path.exists(schema_path):
        with open(schema_path) as f:
            sql = f.read()
            # Strip AlloyDB-specific extensions not in standard PG
            sql = sql.replace("CREATE EXTENSION IF NOT EXISTS google_ml_integration;", "")
            sql = sql.replace("vector(768)", "text")  # mock embeddings as text
            sql = sql.replace("USING scann(embedding cosine) WITH (num_leaves=10);", "")
            for statement in sql.split(";"):
                if statement.strip():
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(statement))
                            conn.commit()
                    except Exception:
                        pass  # Ignore errors in test setup
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Transactional fixture — each test runs in a transaction
    that is rolled back after the test. Keeps tests isolated.
    """
    with db_engine.connect() as conn:
        transaction = conn.begin()
        yield conn
        transaction.rollback()


# ── BigQuery emulator container ───────────────────────────────────────────

@pytest.fixture(scope="session")
def bigquery_container():
    """
    Spins up the official Google BigQuery emulator.
    Image: ghcr.io/goccy/bigquery-emulator
    """
    container = (
        DockerContainer("ghcr.io/goccy/bigquery-emulator:latest")
        .with_bind_ports(9050, 9050)
        .with_bind_ports(9060, 9060)
        .with_command("--project=arc-test-project --dataset=arc_dataset")
    )
    with container:
        # Wait for emulator to be ready
        time.sleep(3)
        # Set env vars so BigQuery client hits emulator
        os.environ["BIGQUERY_EMULATOR_HOST"] = "localhost:9050"
        os.environ["GOOGLE_CLOUD_PROJECT"] = "arc-test-project"
        yield container
        del os.environ["BIGQUERY_EMULATOR_HOST"]


@pytest.fixture(scope="session")
def bq_client(bigquery_container):
    """BigQuery client pointed at the emulator."""
    from google.cloud import bigquery
    from google.auth.credentials import AnonymousCredentials
    
    client = bigquery.Client(
        project="arc-test-project",
        credentials=AnonymousCredentials(),
        client_options={"api_endpoint": "http://localhost:9050"}
    )
    # Create test dataset and tables
    try:
        dataset = bigquery.Dataset("arc-test-project.arc_dataset")
        client.create_dataset(dataset, exists_ok=True)
    except Exception:
        pass  # Dataset may already exist
    yield client


# ── Mock clients for unit tests ───────────────────────────────────────────

@pytest.fixture
def mock_alloydb():
    """Mock AlloyDB client for unit tests."""
    from tools.shared.alloydb_client import MockAlloyDBClient
    return MockAlloyDBClient()


@pytest.fixture
def mock_bigquery():
    """Mock BigQuery client for unit tests."""
    from unittest.mock import MagicMock
    return MagicMock()
