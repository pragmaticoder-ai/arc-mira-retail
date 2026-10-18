"""Environment configuration. Google infrastructure is the default runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


def _bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # ── Mode ─────────────────────────────────────────────────────────
    # True -> explicit offline test fixtures only
    # False -> adapters call real AlloyDB / BigQuery / Vertex AI
    use_mock: bool = _bool("USE_MOCK", False)

    # Optional HTTP mock server. When set, mock adapters route through it
    # (simulating real API calls over the wire). When unset, mocks run
    # in-process. Ignored entirely when use_mock is False.
    mock_server_url: str | None = os.getenv("MOCK_SERVER_URL") or None

    # ── Google Cloud (used only when use_mock is False) ──────────────
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "aria-mira-retail")
    google_cloud_region: str = os.getenv("GOOGLE_CLOUD_REGION", "asia-southeast1")

    # ── AlloyDB ──────────────────────────────────────────────────────
    alloydb_host: str = os.getenv("ALLOYDB_HOST", "127.0.0.1")
    alloydb_port: int = int(os.getenv("ALLOYDB_PORT", "5432"))
    alloydb_database: str = os.getenv("ALLOYDB_DATABASE", "postgres")
    alloydb_user: str = os.getenv("ALLOYDB_USER", "postgres")
    # Secret Manager is supported locally and in production.
    alloydb_password: str = os.getenv("ALLOYDB_PASSWORD", "")

    cloud_sql_instance: str = os.getenv("CLOUD_SQL_INSTANCE", "")
    db_password_secret: str = os.getenv("DB_PASSWORD_SECRET", "")

    # ── BigQuery ─────────────────────────────────────────────────────
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "arc_dataset")
    bigquery_location: str = os.getenv("BIGQUERY_LOCATION", "asia-southeast1")

    # Optional file-backed SQLite bridge (stdlib) so ARIA and PULSE running in
    # SEPARATE processes share the incidents bridge for a live cross-app demo.
    # Unset -> in-process mock dict (default; used by tests). Set to a file path
    # (e.g. data/arc_bridge.db) and point both processes at it. Real BigQuery
    # takes over unchanged when USE_MOCK=false.
    arc_bridge_db: str | None = os.getenv("ARC_BRIDGE_DB") or None

    # Shared operational state (sessions, inventory, decisions, orders).
    arc_state_db: str | None = os.getenv("ARC_STATE_DB") or (str(os.getenv("ARC_BRIDGE_DB")) + ".state" if os.getenv("ARC_BRIDGE_DB") else None)
    demo_date: str | None = os.getenv("DEMO_DATE") or None

    # ── Vertex AI / Gemini ───────────────────────────────────────────
    vertex_ai_location: str = os.getenv("VERTEX_AI_LOCATION", "asia-southeast1")
    gemini_pro_model: str = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-flash")
    gemini_flash_model: str = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "768"))

    default_store_id: str | None = os.getenv("DEFAULT_STORE_ID") or None

    # ── Rate limiting ────────────────────────────────────────────────
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    rate_limit_burst: int = int(os.getenv("RATE_LIMIT_BURST", "10"))

    # ── Environment ──────────────────────────────────────────────────
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self) -> None:
        if self.use_mock and self.arc_state_db and self.arc_bridge_db and Path(self.arc_state_db).resolve() == Path(self.arc_bridge_db).resolve():
            raise ValueError("ARC_STATE_DB and ARC_BRIDGE_DB must use different files")


settings = Settings()
