# ARC — Agentic Retail Command

ARC preserves the demand a completed sale can hide. A shopper accepts an
alternative *for this week*; the original preference stays visible to the store
manager, who can review evidence, choose an action, and observe later outcomes.

**Team:** Pragmatic Engineers · **Theme:** Retail & Commerce

## What works in this branch

- **ARIA:** stateful shopping, explicit dietary and budget constraints, live local
  inventory, substitution feedback, reviewed quotes, validated checkout, and
  idempotent order creation.
- **PULSE:** customer statements behind unmet demand, separate counts for satisfied
  alternatives and temporary compromises, comparison of transfer / replenishment /
  defer options, persistent manager decisions, and subsequent fulfillment counts.
- **Shared local storage:** SQLite persists operational data and incidents across
  app processes and restarts. A manager-approved discount changes the shopper's
  catalog and price. A simulated inventory transfer makes the original product
  available for the next local shopper.

The local orchestration and feedback parser are deterministic rules, **not live
Gemini execution**. Google SDK/ADK execution, AlloyDB, BigQuery ML, and deployment
are deferred integrations. `USE_MOCK=false` does not turn them on. The architecture
and deployment documents distinguish working local behavior from the intended
cloud system; they do not claim a completed cloud deployment. SQLite is a single-host prototype, not shared storage across
independently deployed Cloud Run instances.

## Run the complete local prototype

Use Python 3.11+ and Node 18.17+ with npm. From the repository root:

```bash
uv sync --group dev
uv pip install -r frontend/pulse-dashboard/requirements.txt
npm --prefix frontend/aria-app ci
.venv/bin/python scripts/run_local.py
```

Open the store at **http://localhost:3000** and PULSE at
**http://localhost:8501**. The launcher starts ARIA at `127.0.0.1:8001`, configures
both apps to use the same local stores, and shuts down its children on Ctrl+C.
The store always calls the backend; it never silently substitutes a fake order.

The launcher uses `data/local/incidents.sqlite` and
`data/local/operations.sqlite`. To run an independent fresh demo without deleting
existing data:

```bash
.venv/bin/python scripts/run_local.py --data-dir /tmp/arc-fresh-demo
```

If the usual ports are occupied, pass `--web-port 3100 --aria-port 8002
--pulse-port 8502`. Each launcher uses an isolated Next.js build directory.

For separate terminals, export the same **absolute** `ARC_BRIDGE_DB` and
`ARC_STATE_DB` paths in each Python service, set `USE_MOCK=true`, and set the
Next.js `ARIA_AGENT_URL` to the ARIA service URL. Never use the same SQLite file
for both databases: their transactions use separate connections.

## Try the distinguishing workflow

1. Ask ARIA: **“Weekly halal groceries, family of 4, AED 300. Include brown rice.”**
2. Choose **Temporary compromise** for the proposed alternative. Review and
   confirm the basket. The order succeeds; the original preference remains unmet.
3. Open PULSE. Inspect the customer evidence and distinguish your live local
   session from the labeled synthetic seed sessions.
4. Compare actions and approve **transfer**. This simulates a stock movement
   while preserving the source store's safety stock.
5. Start a new shopper session (Continue shopping after checkout) and request
   **“Brown rice please, AED 30.”** Confirm it. PULSE shows an observed fulfilled
   request after the decision. This is descriptive monitoring, not causal proof.
6. Approve the Laban discount in PULSE. The store catalog refreshes within ten
   seconds. A new Laban request quotes the approved price.

See [the three-minute demo](docs/DEMO.md), [review fixes and limitations](docs/REVIEW_FIXES.md),
and [evaluation](docs/EVALUATION.md).

## Validate

```bash
.venv/bin/python -m pytest
.venv/bin/ruff check agents tools frontend/pulse-dashboard scripts tests
.venv/bin/mypy agents tools frontend/pulse-dashboard/data_provider.py
.venv/bin/python -m scripts.evaluate_demand
npm --prefix frontend/aria-app run build
```

Tests cover real endpoint-to-storage behavior, separate processes, concurrent
checkout, rollback, stale quotes, explicit customer evidence, action idempotency,
and the manager-to-shopper loop. All customer and velocity seed data is synthetic;
modeled revenue is labeled as an estimate. No retail performance claim is made.


## Specifications and implementation status

[ARC_SPEC.md](ARC_SPEC.md) is the current product specification (1.1).
[ARCHITECTURE.md](ARCHITECTURE.md), [DATA_MODEL.md](DATA_MODEL.md) and
[AGENT_CONTRACTS.md](AGENT_CONTRACTS.md) describe actual local execution and
explicit future integration boundaries. [The specification index](specs/README.md)
links the tool/workflow details and generated OpenAPI snapshots. Operational setup
is in [DEPLOYMENT.md](DEPLOYMENT.md); contribution checks are in
[CONTRIBUTING.md](CONTRIBUTING.md). Google-oriented assets remain planned work.
