# SPEC-00 — Project Setup & Dependencies
> MIRA Retail · ARC Project · Backend Specification
> Version 1.0

---

## Overview

This spec covers the complete project setup for the ARC backend — package management, dependency declaration, project structure, toolchain configuration, and the local development environment including Testcontainers for integration testing.

All backend code is Python 3.11. Tools are served as FastAPI endpoints deployed on Cloud Run. Agents are wired using Google ADK.

---

## 1. Package manager — uv

We use `uv` (not pip) for all dependency management. uv is 10-100x faster than pip, generates a lockfile, and manages virtual environments automatically.

### Install uv (one-time, both engineers)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart terminal after install
uv --version   # should print uv 0.x.x
```

### Project initialisation

```bash
cd arc-mira-retail

# Initialise uv workspace
uv init --python 3.11

# This creates:
# pyproject.toml  ← single source of truth for all dependencies
# uv.lock         ← lockfile (commit this)
# .python-version ← pins 3.11 (commit this)
```

---

## 2. pyproject.toml — canonical dependency file

```toml
[project]
name = "arc-mira-retail"
version = "1.0.0"
description = "ARC — Agentic Retail Command for MIRA Retail"
requires-python = ">=3.11"

[project.dependencies]
# ── Agent framework ──────────────────────────────────────────
google-adk = ">=1.0.0"

# ── Google Cloud ─────────────────────────────────────────────
google-cloud-aiplatform = ">=1.60.0"
google-cloud-bigquery = ">=3.20.0"
google-cloud-bigquery-storage = ">=2.25.0"
google-cloud-alloydb-connector = ">=1.0.0"
google-cloud-secret-manager = ">=2.20.0"
google-cloud-logging = ">=3.10.0"

# ── Database ─────────────────────────────────────────────────
pg8000 = ">=1.31.0"
sqlalchemy = ">=2.0.0"

# ── API framework ────────────────────────────────────────────
fastapi = ">=0.111.0"
uvicorn = {extras = ["standard"], version = ">=0.30.0"}
slowapi = ">=0.1.9"

# ── Auth ─────────────────────────────────────────────────────
google-auth = ">=2.29.0"
google-auth-httpx = ">=0.1.0"

# ── Data validation ──────────────────────────────────────────
pydantic = ">=2.7.0"
pydantic-settings = ">=2.3.0"

# ── HTTP client ──────────────────────────────────────────────
httpx = ">=0.27.0"

# ── Utilities ────────────────────────────────────────────────
python-dotenv = ">=1.0.0"
structlog = ">=24.2.0"
tenacity = ">=8.3.0"

[dependency-groups]
dev = [
  # ── Testing ──────────────────────────────────────────────
  "pytest>=8.2.0",
  "pytest-asyncio>=0.23.0",
  "pytest-cov>=5.0.0",
  "pytest-mock>=3.14.0",
  "respx>=0.21.0",
  "factory-boy>=3.3.0",
  "faker>=25.0.0",
  # ── Testcontainers ───────────────────────────────────────
  "testcontainers>=4.7.0",
  "testcontainers-postgres>=0.0.1rc1",
  # ── Linting / typing ─────────────────────────────────────
  "ruff>=0.4.0",
  "mypy>=1.10.0",
  "types-requests>=2.32.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=tools --cov-report=term-missing --cov-fail-under=80"
markers = [
  "unit: pure unit tests, no external dependencies",
  "integration: requires Docker + Testcontainers",
  "contract: validates tool I/O against AGENT_CONTRACTS.md",
]

[tool.ruff]
target-version = "py311"
line-length = 88
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.coverage.run]
omit = ["tests/*", "*/__init__.py"]
```

---

## 3. Install all dependencies

```bash
# Install all deps including dev group
uv sync --all-groups

# Verify
uv run python --version        # Python 3.11.x
uv run pytest --version        # pytest 8.x.x
uv run ruff --version          # ruff 0.x.x
```

---

## 4. Project structure — full backend layout

```
arc-mira-retail/
│
├── pyproject.toml              ← uv dependency declaration
├── uv.lock                     ← lockfile (commit)
├── .python-version             ← 3.11 pin (commit)
├── .env.example                ← env var template
├── .env                        ← local values (gitignored)
│
├── tools/
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── alloydb_client.py   ← AlloyDB connection pool
│   │   ├── bigquery_client.py  ← BigQuery client wrapper
│   │   ├── models.py           ← Pydantic models (shared)
│   │   ├── auth.py             ← IAM token verification middleware
│   │   ├── rate_limit.py       ← Rate limiter (slowapi)
│   │   └── logger.py           ← Structured logging (structlog)
│   │
│   ├── aria_tools/
│   │   ├── __init__.py
│   │   ├── main.py             ← FastAPI app for ARIA tools
│   │   ├── parse_intent.py
│   │   ├── get_customer_context.py
│   │   ├── build_cart.py
│   │   ├── check_stock.py
│   │   ├── suggest_substitution.py
│   │   ├── optimize_budget.py
│   │   ├── apply_promotion.py
│   │   ├── place_order.py
│   │   └── log_session.py
│   │
│   ├── pulse_tools/
│   │   ├── __init__.py
│   │   ├── main.py             ← FastAPI app for PULSE tools
│   │   ├── detect_patterns.py
│   │   ├── find_root_cause.py
│   │   ├── predict_stockout.py
│   │   ├── calculate_impact.py
│   │   ├── draft_purchase_order.py
│   │   └── execute_perishable_discount.py
│   │
│   └── Dockerfile              ← shared tools container
│
├── agents/
│   ├── aria/
│   │   ├── agent.py            ← ADK agent definition
│   │   ├── system_prompt.txt
│   │   ├── tools.py            ← FunctionTool bindings
│   │   ├── main.py             ← Cloud Run entry point
│   │   ├── Dockerfile
│   │   └── requirements.txt    ← agent-specific deps
│   └── pulse/
│       ├── agent.py
│       ├── system_prompt.txt
│       ├── tools.py
│       ├── main.py
│       ├── Dockerfile
│       └── requirements.txt
│
├── data/
│   ├── schema/
│   │   ├── alloydb_schema.sql
│   │   └── bigquery_schema.sql
│   └── seed/
│       ├── customer_profiles.sql
│       ├── inventory.sql
│       ├── promotions.sql
│       └── replenishment.sql
│
└── tests/
    ├── conftest.py             ← shared fixtures, Testcontainers setup
    ├── factories.py            ← factory-boy model factories
    ├── unit/
    │   ├── aria/
    │   │   ├── test_parse_intent.py
    │   │   ├── test_get_customer_context.py
    │   │   ├── test_build_cart.py
    │   │   ├── test_check_stock.py
    │   │   ├── test_suggest_substitution.py
    │   │   ├── test_optimize_budget.py
    │   │   ├── test_apply_promotion.py
    │   │   ├── test_place_order.py
    │   │   └── test_log_session.py
    │   ├── pulse/
    │   │   ├── test_detect_patterns.py
    │   │   ├── test_find_root_cause.py
    │   │   ├── test_predict_stockout.py
    │   │   ├── test_calculate_impact.py
    │   │   ├── test_draft_purchase_order.py
    │   │   └── test_execute_perishable_discount.py
    │   └── shared/
    │       ├── test_models.py
    │       ├── test_auth.py
    │       └── test_rate_limit.py
    ├── integration/
    │   ├── test_alloydb_client.py
    │   ├── test_bigquery_client.py
    │   ├── test_aria_tools_integration.py
    │   ├── test_pulse_tools_integration.py
    │   └── test_bridge.py      ← ARIA writes → PULSE reads
    └── contract/
        ├── test_aria_contracts.py
        └── test_pulse_contracts.py
```

---

## 5. Testcontainers — local integration testing

We use Testcontainers to spin up real PostgreSQL and BigQuery emulator containers locally for integration tests. No mocking — real queries against real (local) databases.

### Prerequisites

```bash
# Install Docker Desktop for Mac
# https://www.docker.com/products/docker-desktop/
# Ensure Docker is running before running integration tests

docker --version   # Docker 25.x.x or higher
docker ps          # Should list running containers
```

### conftest.py — shared fixtures

```python
# tests/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.core.container import DockerContainer
from sqlalchemy import create_engine, text
import os

# ── PostgreSQL container (AlloyDB-compatible) ──────────────────────────

@pytest.fixture(scope="session")
def postgres_container():
    """
    Spins up a PostgreSQL 15 container for the test session.
    AlloyDB is PostgreSQL-compatible — all schema/queries work identically.
    Container is reused across all integration tests in the session.
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
    with engine.connect() as conn:
        schema_path = "data/schema/alloydb_schema.sql"
        with open(schema_path) as f:
            # Strip AlloyDB-specific extensions not in standard PG
            sql = f.read()
            sql = sql.replace("CREATE EXTENSION IF NOT EXISTS google_ml_integration;", "")
            sql = sql.replace("vector(768)", "text")  # mock embeddings as text
            sql = sql.replace("USING scann(embedding cosine) WITH (num_leaves=10);", "")
            for statement in sql.split(";"):
                if statement.strip():
                    conn.execute(text(statement))
        conn.commit()
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

# ── BigQuery emulator container ────────────────────────────────────────

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
        import time
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
    dataset = bigquery.Dataset("arc-test-project.arc_dataset")
    client.create_dataset(dataset, exists_ok=True)
    yield client
```

---

## 6. Environment configuration

### .env.example

```env
# Google Cloud
GOOGLE_CLOUD_PROJECT=mira-arc-hackathon
GOOGLE_CLOUD_REGION=asia-southeast1

# AlloyDB
ALLOYDB_HOST=127.0.0.1
ALLOYDB_PORT=5432
ALLOYDB_DATABASE=postgres
ALLOYDB_USER=postgres
ALLOYDB_PASSWORD=your-password

# BigQuery
BIGQUERY_DATASET=arc_dataset
BIGQUERY_LOCATION=asia-southeast1

# Vertex AI
VERTEX_AI_LOCATION=asia-southeast1
GEMINI_PRO_MODEL=gemini-1.5-pro
GEMINI_FLASH_MODEL=gemini-1.5-flash-001

# Auth
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Environment
ENVIRONMENT=development   # development | staging | production
LOG_LEVEL=INFO
```

### Settings model (pydantic-settings)

```python
# tools/shared/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Google Cloud
    google_cloud_project: str
    google_cloud_region: str = "asia-southeast1"

    # AlloyDB
    alloydb_host: str
    alloydb_port: int = 5432
    alloydb_database: str = "postgres"
    alloydb_user: str = "postgres"
    alloydb_password: str

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

settings = Settings()
```

---

## 7. FastAPI app structure (shared pattern)

Every tool module (aria_tools, pulse_tools) exposes a FastAPI app:

```python
# tools/aria_tools/main.py
from fastapi import FastAPI, Depends, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from tools.shared.auth import verify_iam_token
from tools.shared.logger import get_logger

logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="ARC ARIA Tool Functions",
    version="1.0.0",
    description="ARIA agent tool functions for MIRA Retail"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register all ARIA tool routes
from tools.aria_tools import (
    parse_intent, get_customer_context, build_cart,
    check_stock, suggest_substitution, optimize_budget,
    apply_promotion, place_order, log_session
)

app.include_router(parse_intent.router, dependencies=[Depends(verify_iam_token)])
app.include_router(get_customer_context.router, dependencies=[Depends(verify_iam_token)])
app.include_router(build_cart.router, dependencies=[Depends(verify_iam_token)])
app.include_router(check_stock.router, dependencies=[Depends(verify_iam_token)])
app.include_router(suggest_substitution.router, dependencies=[Depends(verify_iam_token)])
app.include_router(optimize_budget.router, dependencies=[Depends(verify_iam_token)])
app.include_router(apply_promotion.router, dependencies=[Depends(verify_iam_token)])
app.include_router(place_order.router, dependencies=[Depends(verify_iam_token)])
app.include_router(log_session.router, dependencies=[Depends(verify_iam_token)])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "arc-aria-tools"}
```

---

## 8. Non-functional requirements — baseline

### Auth

```python
# tools/shared/auth.py
from fastapi import Request, HTTPException, status
import google.auth.transport.requests
import google.oauth2.id_token

async def verify_iam_token(request: Request) -> dict:
    """
    Verifies Google Cloud IAM Bearer token on every request.
    Rejects requests without a valid token with 401.
    In development (ENVIRONMENT=development), bypasses verification.
    """
    from tools.shared.settings import settings

    if settings.environment == "development":
        return {"sub": "dev-user", "email": "dev@mira.ae"}

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = auth_header.split(" ")[1]
    try:
        id_info = google.oauth2.id_token.verify_oauth2_token(
            token,
            google.auth.transport.requests.Request()
        )
        return id_info
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
```

### Rate limiting

```python
# tools/shared/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from tools.shared.settings import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)

# Per-endpoint limits:
# - parse_intent:          60/minute (lightweight)
# - build_cart:            30/minute (DB heavy)
# - place_order:           10/minute (write operation)
# - log_session:           60/minute (write, always called)
# - detect_patterns:       10/minute (BQ heavy)
# - draft_purchase_order:  5/minute  (write, manager action)
```

### Structured logging

```python
# tools/shared/logger.py
import structlog
from tools.shared.settings import settings

def get_logger(name: str):
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
    return structlog.get_logger(name)
```

### Retry logic (tenacity)

```python
# Applied to all DB calls and external API calls
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def db_query_with_retry(query, params):
    ...
```

---

## 9. Toolchain commands reference

```bash
# Install all deps
uv sync --all-groups

# Run all tests
uv run pytest

# Run only unit tests (no Docker needed)
uv run pytest -m unit

# Run only integration tests (Docker required)
uv run pytest -m integration

# Run only contract tests
uv run pytest -m contract

# Run with coverage report
uv run pytest --cov=tools --cov-report=html

# Lint
uv run ruff check tools/ tests/

# Type check
uv run mypy tools/

# Run ARIA tools locally
uv run uvicorn tools.aria_tools.main:app --reload --port 8001

# Run PULSE tools locally
uv run uvicorn tools.pulse_tools.main:app --reload --port 8002

# Format code
uv run ruff format tools/ tests/
```

---

## 10. Dockerfile — shared tools container

```dockerfile
# tools/Dockerfile
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install production deps only (no dev group)
RUN uv sync --frozen --no-dev

# Copy source
COPY tools/ ./tools/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

# Set by Cloud Run deployment (aria or pulse)
ARG AGENT_TYPE=aria
ENV AGENT_TYPE=$AGENT_TYPE

CMD ["sh", "-c", "uv run uvicorn tools.${AGENT_TYPE}_tools.main:app --host 0.0.0.0 --port 8080"]
```

---

*MIRA Retail · ARC v1.0 · SPEC-00 Project Setup v1.0*
