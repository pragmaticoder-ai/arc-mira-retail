"""Pydantic settings management for ARC backend.

All configuration comes from environment variables, with sensible defaults
for local development. In production, secrets come from Secret Manager.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Google Cloud
    google_cloud_project: str = "mira-arc-hackathon"
    google_cloud_region: str = "asia-southeast1"

    # AlloyDB
    alloydb_host: str = "127.0.0.1"
    alloydb_port: int = 5432
    alloydb_database: str = "postgres"
    alloydb_user: str = "postgres"
    alloydb_password: str = ""

    # BigQuery
    bigquery_dataset: str = "arc_dataset"
    bigquery_location: str = "asia-southeast1"

    # Vertex AI
    vertex_ai_location: str = "asia-southeast1"
    gemini_pro_model: str = "gemini-1.5-pro"
    gemini_flash_model: str = "gemini-1.5-flash-001"

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # Mock mode (for local development without GCP)
    use_mock: bool = True
    mock_server_url: str = "http://localhost:8900"

    # Tool service URLs (set after Cloud Run deploy)
    aria_tools_url: str = ""
    pulse_tools_url: str = ""


settings = Settings()
