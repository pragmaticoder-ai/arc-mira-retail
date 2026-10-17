"""Env-backed settings for ARC backend tools.

All configuration comes from environment variables so the same code runs
locally (mock mode) and in Cloud Run (real GCP, values from Secret Manager).
Nothing is hardcoded. Flip USE_MOCK=false and supply real GCP settings to
switch every adapter from mock to live — no code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # ── Mode ─────────────────────────────────────────────────────────
    # True  -> adapters use in-process mocks / the local mock server
    # False -> adapters call real AlloyDB / BigQuery / Vertex AI
    use_mock: bool = _bool("USE_MOCK", True)

    # Optional HTTP mock server. When set, mock adapters route through it
    # (simulating real API calls over the wire). When unset, mocks run
    # in-process. Ignored entirely when use_mock is False.
    mock_server_url: str | None = os.getenv("MOCK_SERVER_URL") or None

    # ── Google Cloud (used only when use_mock is False) ──────────────
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "mira-arc-hackathon")
    google_cloud_region: str = os.getenv("GOOGLE_CLOUD_REGION", "asia-southeast1")

    # ── AlloyDB ──────────────────────────────────────────────────────
    alloydb_host: str = os.getenv("ALLOYDB_HOST", "127.0.0.1")
    alloydb_port: int = int(os.getenv("ALLOYDB_PORT", "5432"))
    alloydb_database: str = os.getenv("ALLOYDB_DATABASE", "postgres")
    alloydb_user: str = os.getenv("ALLOYDB_USER", "postgres")
    # Real password is sourced from Secret Manager in production, never code.
    alloydb_password: str = os.getenv("ALLOYDB_PASSWORD", "")

    # ── BigQuery ─────────────────────────────────────────────────────
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "arc_dataset")
    bigquery_location: str = os.getenv("BIGQUERY_LOCATION", "asia-southeast1")

    # ── Vertex AI / Gemini ───────────────────────────────────────────
    vertex_ai_location: str = os.getenv("VERTEX_AI_LOCATION", "asia-southeast1")
    gemini_pro_model: str = os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro")
    gemini_flash_model: str = os.getenv("GEMINI_FLASH_MODEL", "gemini-1.5-flash-001")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "textembedding-gecko@003")
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "768"))

    # ── Environment ──────────────────────────────────────────────────
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
