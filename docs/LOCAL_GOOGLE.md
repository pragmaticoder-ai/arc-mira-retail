# Run locally with Google infrastructure

All four apps run on your machine. PostgreSQL, BigQuery, Gemini and embeddings
use Google Cloud. The default launcher never selects SQLite or a canned model.
Offline fixtures remain available only through `--offline` and automated tests.

## Provision once

The development configuration follows the infrastructure branch's Cloud SQL
PostgreSQL option. This creates a billed `db-f1-micro` instance in Singapore;
review its costs in Cloud Billing. No Cloud Run services or VPC connector are
required for local execution. Do not run Terraform against these same resources
without importing them into its state first.

```bash
uv sync
gcloud auth application-default login
gcloud auth application-default set-quota-project aria-mira-retail
bash scripts/deploy_gcp.sh aria-mira-retail asia-southeast1 --local-only
```

Wait for `arc-postgres-instance` to become `RUNNABLE`, then:

```bash
.venv/bin/python scripts/provision_local_gcp.py --project aria-mira-retail --finish
.venv/bin/python scripts/init_gcp_db.py --seed --embed
.venv/bin/python scripts/run_local.py
```

The finish step creates the database, database user and Secret Manager password,
and writes ignored `.env` configuration containing resource names. Passwords
stay in Secret Manager. The Cloud SQL Python connector uses ADC and encrypted
public-IP connectivity; no authorized network or local proxy is needed. Your
identity needs Cloud SQL Client, Secret Accessor, Vertex AI User, BigQuery Job
User and dataset data access. Provisioning additionally requires resource admin
permissions. A private-IP-only database requires a separate network path.

The explicit `--seed` option loads the repository's **sample catalog/customer
personas**, without synthetic shopper incidents. It preserves existing rows;
rerunning it does not restore purchased stock or overwrite approvals. `--embed`
generates missing 768-dimensional Google embeddings in PostgreSQL. Schema and
embedding failures stop initialization rather than printing success.

## Local URLs

- Storefront: <http://localhost:3000>
- ARIA API: <http://localhost:8001/docs>
- PULSE API: <http://localhost:8002/docs>
- Manager dashboard: <http://localhost:8501>

Ctrl+C stops the local processes. Cloud SQL continues running and billing until
stopped/deleted separately. Local services bind to loopback; the demo customer
selector is not production authentication.

## Implemented integration

ARIA uses Google ADK and Gemini for conversation and structured basket proposals
grounded in the store catalog. Questions and clarification preserve the basket,
quote and shopping constraints; only explicit shopping changes generate a new
basket. Recent conversation turns are persisted with the shopper session. The backend validates identifiers, quantities, diet, exclusions,
budget and current prices. Only an explicit confirmation with the current quote
can place an order. The model has no checkout or manager-write tools. Business
state survives app restarts in PostgreSQL; per-invocation ADK context is temporary.

Inventory, profiles, promotions and schedules use their SQL tables. Sessions,
orders, purchase orders and manager decisions use individual JSONB records in
`arc_records`; the legacy SQL `orders`/`purchase_orders` tables are not written by
this runtime. A transaction advisory lock serializes retail mutations for this
small demo. It is not a high-throughput persistence design.

Substitutions use Google text embeddings and PostgreSQL pgvector cosine search
with stock, diet and price filters. Gemini then verifies culinary equivalence
among retrieved candidates; matching brands or categories alone is insufficient. PULSE computes evidence and proposals from
actual stored sessions and can generate a Gemini summary via `/pulse/analyze`.
The dashboard reads the same data directly; its **Generate Google analysis**
button requests a Gemini summary without regenerating one on every refresh.

BigQuery uses an upsert per session, so feedback and checkout update the same
record. No seeded incident counts or canned sales velocities enter Google mode.
With insufficient history, stockout dates are suppressed; ARIMA training is
separate. Operational writes and BigQuery writes are not an atomic distributed
transaction: failed logging is surfaced through `session_logged=false` and may
be retried, but a durable outbox remains future work.

Recipe requests can be interpreted by Gemini, but there is not yet a curated
recipe database or deterministic ingredient/pack scaling service. Do not claim
recipe completeness from the current cart planner. Supplier dispatch, payment,
physical transfers and delivery remain outside the prototype.

## Offline regression demo

```bash
.venv/bin/python scripts/run_local.py --offline --data-dir /tmp/arc-offline-01
```

This explicitly uses seeded fixtures and local rules. It does not verify Google
connectivity. Automated tests isolate these fixtures from your cloud database.

## Verification on October 18, 2026

Provisioned `arc-postgres-instance` in `aria-mira-retail`, Singapore, plus
`arc_dataset` and the `arc-db-password` secret. Loaded 53 inventory rows across
three stores, with 768-dimensional Google embeddings for every inventory row.
Verified the real storefront HTTP flow: profile/catalog loading, Gemini basket,
canonical quote, confirmed order, single stock decrement and idempotent retry.
Verified Google pgvector retrieval plus Gemini suitability checking (brown rice
to Basmati), explicit compromise feedback, BigQuery session upsert, and PULSE's
Gemini summary. Temporary verification sessions/orders were removed afterward.

The regression suite has 147 passing tests; Ruff, mypy on changed backend code,
and the storefront production build pass. No Chrome installation is required.
Cold Google-backed requests can take tens of seconds; the local launcher uses a
120-second storefront timeout. Cloud Run deployment was not exercised by this
local setup.

Question handling was also verified with real Gemini: price and halal follow-ups
preserve the existing basket and quote; an explicit quantity change creates a
new quote. Informational turns do not emit demand or checkout events.

## Enriched MIRA catalog

See [CATALOG.md](CATALOG.md) for product imports, pagination, attributes,
and product details. Imports enrich the existing Dubai Marina MIRA store.

## Hosted applications

See [CLOUD_RUN.md](CLOUD_RUN.md) for deployment, access, URLs and end-to-end testing.
