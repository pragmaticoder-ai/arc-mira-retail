# SPEC-00 — Project setup and operating contract

Updated October 18, 2026 · Specification 1.1

## 1. Current system

Python 3.11+ FastAPI tools/orchestration, Next.js 14 shopper UI, Streamlit manager
UI, local TF-IDF/rules, and two SQLite stores. Installed Google packages and agent
definitions are scaffolding; real SDK execution/adapters remain deferred.

## 2. Setup

```bash
uv sync --group dev
uv pip install -r frontend/pulse-dashboard/requirements.txt
npm --prefix frontend/aria-app ci
.venv/bin/python scripts/run_local.py
```

Run from the repository root. The launcher starts three services and sets shared
absolute paths. See [DEPLOYMENT.md](../DEPLOYMENT.md) for ports, alternate data
directories, separate terminals and environment behavior. No cloud credentials,
Docker or BigQuery emulator are needed for these local checks.

## 3. Module contracts

- Functions return JSON-serializable success/error dictionaries.
- Shared models and TypeScript interfaces document boundaries; not every legacy
  dict is validated by every shared model at runtime.
- HTTP request models expose only their declared fields. Do not assume Python
  keyword additions automatically become a remote API.
- Server pricing/stock is authoritative. UI edits invalidate quotes and promotions.
- Backend sessions, order idempotency and manager decisions must be persisted.
- Incident upserts retain the original event timestamp and latest session outcome.

## 4. Data and transactions

ARC_STATE_DB and ARC_BRIDGE_DB use different files. Memory mode is test/process
local. Operational writes are atomic within one store; incident delivery has a
separate transaction. Synthetic seeds, simulated transfers and estimated impact
must retain their labels. Business dates use Asia/Dubai with optional DEMO_DATE;
wall-clock timestamps are not frozen by that override.

## 5. Verification

```bash
.venv/bin/python -m pytest
.venv/bin/ruff check agents tools frontend/pulse-dashboard scripts tests
.venv/bin/mypy agents tools frontend/pulse-dashboard/data_provider.py
.venv/bin/python -m scripts.evaluate_demand
npm --prefix frontend/aria-app run build
```

Tests use memory and temporary SQLite; process-isolation tests invoke local child
processes. Dashboard AppTest requires the separately installed Streamlit dependency.
The curated feedback cases are development fixtures, not a held-out benchmark.

## 6. Runtime boundaries

Development tool endpoints bypass IAM verification. Current agent endpoints and
demo login do not provide production application access control. Shared cloud
storage, authentication/authorization, token audiences, model execution, outbox
delivery and supplier/logistics/payment integrations remain planned work.

## 7. Documentation authority

[ARC_SPEC.md](../ARC_SPEC.md) defines product behavior;
[AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) distinguishes current interfaces;
[DATA_MODEL.md](../DATA_MODEL.md) documents actual storage;
[ARCHITECTURE.md](../ARCHITECTURE.md) separates local execution from cloud plans.
See [README.md](README.md) for the complete specification index.
