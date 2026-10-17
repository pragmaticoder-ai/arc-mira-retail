"""Shared pytest fixtures — SPEC-00 §5.

ARC is mock-first: unit and contract tests run with USE_MOCK=true and need no
Docker. The Testcontainers-based integration fixtures from SPEC-00 §5 are kept
behind the `integration` marker for when the real DB layer is wired.
"""

from __future__ import annotations

import os

import pytest

# Force mock mode for the whole test session before any tool import.
os.environ.setdefault("USE_MOCK", "true")
os.environ.setdefault("ENVIRONMENT", "development")


@pytest.fixture()
def alloydb():
    """Fresh mock AlloyDB client per test (resets in-session writes)."""
    import tools.shared.alloydb_client as mod

    mod._client = None  # reset singleton so each test gets clean state
    client = mod.get_alloydb()
    yield client
    mod._client = None


@pytest.fixture()
def bigquery():
    """Fresh mock BigQuery client per test (resets the incidents bridge)."""
    import tools.shared.bigquery_client as mod

    mod._client = None
    client = mod.get_bigquery()
    yield client
    mod._client = None


@pytest.fixture()
def store_id() -> str:
    return "dubai_marina_01"


@pytest.fixture()
def customer_id() -> str:
    return "sarah_123"
