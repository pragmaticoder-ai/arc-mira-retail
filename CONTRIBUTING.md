# Contributing to ARC

Updated October 18, 2026 · Specification 1.1

## Setup

From the repository root, use Python 3.11+, uv and Node 18.17+:

```bash
uv sync --group dev
uv pip install -r frontend/pulse-dashboard/requirements.txt
npm --prefix frontend/aria-app ci
.venv/bin/python scripts/run_local.py
```

The launcher sets the environment and shared storage for every local app. See
[DEPLOYMENT.md](DEPLOYMENT.md) for alternate ports and separate terminals. Google
credentials and Docker are not required for the current local acceptance checks.

## Working conventions

- Use a feature/, fix/ or data/ branch. Current workflow changes are on
  feature/unmet-demand-loop. Write imperative commit messages.
- Keep unrelated changes out of a commit. Group cross-surface changes when needed
  to preserve a single working contract, such as quote review or manager approval.
- Python tool functions return JSON-serializable dictionaries. Add typed boundary
  models where useful and validate authoritative inventory at quote/checkout.
- Keep business decisions in backend tools/adapters, not UI-only state overrides.
- Never label local rules, synthetic statements or simulated actions as a live
  model, actual customer dataset or real supplier/logistics execution.
- Keep credentials, `.env` files, database files, build output and node_modules
  out of source control. Use a fresh data directory rather than deleting a shared
  demo store when repeating a test.

## Source map

| Change | Primary files |
|---|---|
| Shopper session / quote flow | agents/aria/main.py, tools/shared/pricing.py |
| Intent / feedback rules | tools/aria_tools/parse_intent.py, tools/shared/demand.py |
| Atomic operational writes | tools/shared/alloydb_client.py |
| Incident lifecycle / aggregation | tools/aria_tools/log_session.py, tools/shared/bigquery_client.py |
| Demand proposals / actions / observation | tools/pulse_tools/demand_intelligence.py |
| Customer UI / proxy | frontend/aria-app |
| Manager UI / data provider | frontend/pulse-dashboard |
| Future Google integrations | agents/*/agent.py and Real* adapter implementations |

A setting or installed SDK is not proof that an integration works. Preserve a
clear local/Google boundary while the real execution path remains deferred.

## Validation

```bash
.venv/bin/python -m pytest
.venv/bin/ruff check agents tools frontend/pulse-dashboard scripts tests
.venv/bin/mypy agents tools frontend/pulse-dashboard/data_provider.py
.venv/bin/python -m scripts.evaluate_demand
npm --prefix frontend/aria-app run build
```

Tests exercise behavior, including cross-process SQLite visibility, stock/order
rollback, concurrent checkout, retries, current-quote confirmation, constraints,
explicit compromises, manager decisions and later fulfillment. They do not use
Docker, a BigQuery emulator or a live model. Streamlit tests require the dashboard
requirements; a missing optional dependency can cause that module to be skipped.

When changing checkout or persistence, preserve meaningful concurrency/rollback
coverage. When changing language rules, test ambiguous and negative statements;
a bare acceptance must not become evidence of satisfaction. Do not present the
curated feedback fixture as a held-out benchmark.

## Documentation and API maintenance

- Start at [ARC_SPEC.md](ARC_SPEC.md) and [specs/README.md](specs/README.md).
- Update contracts and tool/workflow specifications when behavior changes. Preserve
  the distinction between Python-only arguments and the Pydantic HTTP model.
- Regenerate service OpenAPI from each FastAPI application's `app.openapi()` after
  changing request models. Generic dict response bodies still need prose and tests.
- Update DATA_MODEL for persisted fields and decisions. A planned SQL DDL edit is
  not a migration of an existing database.
- Keep the three-minute demo and README reproducible. Label fixture origins,
  scenario estimates and simulated actions at the point they are shown.
- Branding guidance lives under frontend/mira-brand; current behavior is described
  by SCREENS.md and the product specification rather than visual mockups.

For documentation-only changes, verify local links, OpenAPI path/schema consistency
and runnable examples. Repeat application tests when behavior or executable assets
change; avoid pretending a prose update is new runtime validation.


### Regenerate OpenAPI snapshots

From the repository root after changing an HTTP request model:

```bash
.venv/bin/python - <<'PYCODE'
from pathlib import Path
import yaml
from agents.aria.main import app as aria
from agents.pulse.main import app as pulse
from tools.aria_tools.main import app as aria_tools
from tools.pulse_tools.main import app as pulse_tools

for name, app in (("aria_agent", aria), ("pulse_agent", pulse),
                  ("aria_tools", aria_tools), ("pulse_tools", pulse_tools)):
    Path(f"specs/openapi_{name}.yaml").write_text(
        yaml.safe_dump(app.openapi(), sort_keys=False, allow_unicode=True, width=100)
    )
PYCODE
```

This updates documentation snapshots only. Keep runtime version values from the
application and verify the result against its `app.openapi()` output.
