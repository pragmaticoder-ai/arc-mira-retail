"""Shared PostgreSQL connection configuration for local ADC and Cloud Run."""

from __future__ import annotations

import atexit
from functools import lru_cache

from sqlalchemy import URL, create_engine

from tools.shared.settings import settings


@lru_cache(maxsize=1)
def get_engine():
    password = settings.alloydb_password
    if settings.db_password_secret:
        from google.cloud import secretmanager

        name = settings.db_password_secret
        if not name.startswith("projects/"):
            name = f"projects/{settings.google_cloud_project}/secrets/{name}/versions/latest"
        if "/versions/" not in name:
            name += "/versions/latest"
        password = (
            secretmanager.SecretManagerServiceClient(transport="rest")
            .access_secret_version(request={"name": name}, timeout=30)
            .payload.data.decode()
        )
    if not password:
        raise ValueError(
            "Set DB_PASSWORD_SECRET or ALLOYDB_PASSWORD for the real database"
        )
    if settings.cloud_sql_instance:
        from google.cloud.sql.connector import Connector, IPTypes

        connector = Connector(ip_type=IPTypes.PUBLIC, refresh_strategy="LAZY")
        engine = create_engine(
            "postgresql+pg8000://",
            pool_pre_ping=True,
            creator=lambda: connector.connect(
                settings.cloud_sql_instance,
                "pg8000",
                user=settings.alloydb_user,
                password=password,
                db=settings.alloydb_database,
            ),
            pool_size=2,
            max_overflow=2,
        )
        # Keep connector alive for the lifetime of its engine.
        engine._arc_connector = connector

        def close():
            engine.dispose()
            connector.close()

        atexit.register(close)
        return engine
    return create_engine(
        URL.create(
            "postgresql+pg8000",
            username=settings.alloydb_user,
            password=password,
            host=settings.alloydb_host,
            port=settings.alloydb_port,
            database=settings.alloydb_database,
        ),
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=2,
    )
