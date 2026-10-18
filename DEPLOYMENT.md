> Runtime update: [Google-backed local execution](docs/LOCAL_GOOGLE.md) describes
> the implemented Google path and its current boundaries. Older offline sections
> below require explicit `USE_MOCK=true` / `--offline`.

# ARC local operation and cloud integration plan

Updated October 18, 2026 · Specification 1.1

## 1. Supported deployment today

The executable prototype runs on one host. It uses deterministic rules and two
local SQLite databases. Google ADK Runner execution, real Google data/model
adapters and a production cloud deployment remain unimplemented. This guide does
not present the old Cloud Run commands as a working deployment recipe.

Prerequisites: Python 3.11+, uv, Node 18.17+ and npm. No Google credentials,
Docker or browser installation are required for the local flow or automated checks.

From the repository root:

```bash
uv sync --group dev
uv pip install -r frontend/pulse-dashboard/requirements.txt
npm --prefix frontend/aria-app ci
.venv/bin/python scripts/run_local.py
```

| Surface | Default URL | Started by launcher? |
|---|---|---|
| Storefront | http://localhost:3000 | Yes |
| ARIA backend | http://127.0.0.1:8001 | Yes |
| PULSE dashboard | http://localhost:8501 | Yes |
| Optional PULSE analysis API | Configure a separate port | No |
| Separate ARIA/PULSE tool HTTP services | Configure separate ports | No |

The launcher binds its services to loopback, sets shared database paths, gives
Next.js an isolated build/configuration directory, and stops its child process
groups on Ctrl+C. It does not stop existing servers on occupied ports.

For an independent fresh demo and alternate ports:

```bash
.venv/bin/python scripts/run_local.py \
  --data-dir /tmp/arc-demo-02 \
  --web-port 3100 --aria-port 8002 --pulse-port 8502
```

Reuse a data directory to preserve prior orders, stock and decisions. Choose a new
one to seed a fresh scenario without deleting existing data.

## 2. Separate-terminal operation

Export the same absolute paths in **each Python process**:

```bash
export USE_MOCK=true
export ENVIRONMENT=development
export ARC_STATE_DB=/tmp/arc-manual/operations.sqlite
export ARC_BRIDGE_DB=/tmp/arc-manual/incidents.sqlite
export PYTHONPATH="$PWD"
```

The paths must differ. Start ARIA from the root:

```bash
.venv/bin/python -m uvicorn agents.aria.main:app --host 127.0.0.1 --port 8001
```

In another terminal with the same environment:

```bash
.venv/bin/python -m streamlit run frontend/pulse-dashboard/pulse_dashboard.py \
  --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

Start the storefront with the matching upstream URL:

```bash
ARIA_AGENT_URL=http://127.0.0.1:8001 npm --prefix frontend/aria-app run dev
```

Backend settings read process environment at import time; restart Python services
after changing it. Copying `.env.example` does not by itself load a root `.env`
into Python. Next.js can read its own `.env.local`; the launcher supplies process
environment directly. PULSE calls tools directly; PULSE_AGENT_URL is unused.

Optional HTTP services, in separate terminals with the shared environment:

```bash
.venv/bin/python -m uvicorn agents.pulse.main:app --host 127.0.0.1 --port 8005
.venv/bin/python -m uvicorn tools.aria_tools.main:app --host 127.0.0.1 --port 8003
.venv/bin/python -m uvicorn tools.pulse_tools.main:app --host 127.0.0.1 --port 8004
```

These are separate applications; their `/health` and `/openapi.json` routes refer
to the particular service. They are not additional requirements for the dashboard.

## 3. Environment reference

| Variable | Default / interpretation |
|---|---|
| USE_MOCK | true; false selects deferred Google paths, not a working live service |
| ENVIRONMENT | development; tool IAM verification is bypassed locally |
| ARC_STATE_DB | Unset → memory; if only ARC_BRIDGE_DB is set, its path plus .state |
| ARC_BRIDGE_DB | Unset → memory; otherwise persistent local incident database |
| ARIA_AGENT_URL | Next.js default http://127.0.0.1:8001 |
| ARIA_AGENT_TOKEN | Optional server-side bearer token forwarded to ARIA; not an automatic token-refresh system |
| ARIA_REQUEST_TIMEOUT_MS | 15000 for the Next.js upstream request |
| DEFAULT_CUSTOMER_ID / DEFAULT_STORE_ID | Proxy defaults sarah_123 / dubai_marina_01; the current storefront explicitly sends its selected store and demo customer |
| PULSE_STORE_ID | Default store for provider calls; the UI passes its selected store explicitly |
| PULSE_REFRESH_SECONDS | 10; a nonpositive value disables timed fragment reruns |
| DEMO_DATE | Optional ISO business date for expiry/promotion/proposal calculations; actual timestamps still use wall clock |
| MOCK_SERVER_URL | Optional simulated generation/embedding HTTP calls; not a bridge-storage selector |
| ARC_NEXT_DIST_DIR / ARC_TSCONFIG_PATH | Optional Next.js isolation; set by the local launcher |
| GOOGLE_CLOUD_*, ALLOYDB_*, BIGQUERY_*, GEMINI_*, EMBEDDING_* | Deferred integration configuration; current defaults are placeholders, not verified model recommendations |

## 4. Validate before recording a demo

```bash
.venv/bin/python -m pytest
.venv/bin/ruff check agents tools frontend/pulse-dashboard scripts tests
.venv/bin/mypy agents tools frontend/pulse-dashboard/data_provider.py
.venv/bin/python -m scripts.evaluate_demand
npm --prefix frontend/aria-app run build
```

The Python suite uses memory/temp SQLite and separate child processes, not cloud
services or a BigQuery emulator. Dashboard tests use Streamlit AppTest when the
separate dashboard dependency is installed. See [docs/DEMO.md](docs/DEMO.md) for
the demonstration and [docs/EVALUATION.md](docs/EVALUATION.md) for measured limits.

## 5. Troubleshooting

| Symptom | Check |
|---|---|
| Storefront says ARIA unavailable | ARIA process and ARIA_AGENT_URL; do not expect a scripted success fallback |
| Dashboard changes do not reach the store | Identical absolute storage paths in both Python processes; restart after env changes |
| PULSE shows process-memory warning | Shared SQLite paths are unset |
| Existing demo starts with approved actions | Reused state is intentional; use a fresh data directory for a clean scenario |
| Ports already occupied | Pass alternate launcher ports; leave existing servers running |
| Quote returns without placing an order | Basket or prices changed, or quote ID is missing; review and confirm the replacement quote |
| USE_MOCK=false fails | Google execution/adapters are deferred; use local mode for this branch |

## 6. Planned Google Cloud rollout

Before publishing an actual cloud prototype:

1. Implement an ADK execution/session path and validate structured model output
   against the current cart, evidence and decision contracts.
2. Implement managed operational storage with atomic checkout and durable
   idempotency; migrate sessions, quotes and manager decisions, not just inventory.
3. Implement outbox-backed incident delivery and BigQuery upsert/deduplication.
   Migrate existing tables explicitly for the new evidence/lifecycle fields.
4. Replace or clearly retain the synthetic forecast/velocity assumptions; evaluate
   predictions before presenting confidence as a measured statistic.
5. Add application authentication/authorization, verified identity audiences,
   managed credentials and token renewal. Local demo login is not that integration.
6. Package each service and verify actual deployment entry points, health/readiness,
   data connectivity, persistence across instances and the complete feedback loop.
7. Validate the demo and submission artifacts against current event requirements.

## 6. Google Cloud deployment infrastructure

Production and cloud-ready infrastructure assets are located in:
- `terraform/`: Complete Terraform configuration (VPC, Cloud SQL / AlloyDB, BigQuery, Artifact Registry, Secret Manager, Cloud Run).
- `cloudbuild.yaml`: Google Cloud Build pipeline for parallel container builds.
- `scripts/setup_gcp_project.sh`: Automated script to check project, link billing, and enable required Google Cloud APIs.
- `scripts/deploy_gcp.sh`: Master one-click deployment script.
- `scripts/init_gcp_db.py`: Database schema and seed loader for PostgreSQL / AlloyDB and BigQuery.
- `docs/GCP_INFRASTRUCTURE.md`: Full architecture specification, topology diagram, and cost-optimization guide.

AlloyDB/BigQuery SQL in `data/schema` and ADK bindings/prompts are starting assets.
Supplier delivery, logistics execution and payments require their own integrations and remain outside the local simulation.
