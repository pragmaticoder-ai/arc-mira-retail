# ARC backend tools — adapter placeholders (mock-first)

This directory is seeded by the frontend engineer as a **clean starting point**
for the backend engineer. It contains the shared adapter layer only — the 9
ARIA + 6 PULSE tool functions are yours to build on top of it (see
`AGENT_CONTRACTS.md` and `specs/SPEC-ARIA-*.md` / `specs/SPEC-PULSE-*.md`).

## The idea: every Google dependency sits behind an interface

No tool talks to a Google SDK directly. Each dependency has an adapter in
`tools/shared/` with two implementations, chosen by the `USE_MOCK` env flag:

| Adapter | Factory | Mock does | Real (TODO) |
|---------|---------|-----------|-------------|
| `alloydb_client` | `get_alloydb()` | in-memory customers/inventory/orders/POs | AlloyDB connector + pg8000 |
| `bigquery_client` | `get_bigquery()` | in-memory incidents bridge + canned ARIMA forecast | BigQuery + BigQuery ML |
| `llm` | `get_llm()` | deterministic Gemini responses | Vertex AI GenerativeModel |
| `embeddings` | `get_embeddings()` | deterministic pseudo-vectors | Vertex AI text embeddings |
| `vector_search` | `get_vector_search()` | in-Python cosine over seed data | AlloyDB AI ScaNN SQL |

Each real implementation is a `NotImplementedError` placeholder marked
`TODO(backend)` at the exact wiring point — search for `TODO(backend)`.

## Why mock-first (no emulators)

- **AlloyDB** could use a Postgres container, but a pure in-memory mock keeps
  the demo fully offline and dependency-free for now.
- **BigQuery ML (ARIMA_PLUS)** has no emulator at all → `forecast_stockout`
  returns a canned prediction in mock mode.
- **Gemini / embeddings / ScaNN** have no local equivalent → mocked.

When you're ready for real GCP, implement the `RealX` classes and flip
`USE_MOCK=false`. No tool code changes — only the adapter internals and env.

## Two mock modes

1. **In-process (default):** mocks compute results in Python. Zero setup.
2. **Over HTTP:** set `MOCK_SERVER_URL` and run the mock server in `mocks/`.
   The `llm`, `embeddings`, and bridge adapters then make real HTTP calls,
   so you can demo the "it's calling an API" path. See `mocks/README.md`.

## Usage from a tool

```python
from tools.shared import get_alloydb, get_bigquery, get_vector_search

def get_customer_context(customer_id: str) -> dict:
    db = get_alloydb()
    customer = db.get_customer(customer_id)
    ...
```

## Config

Copy `.env.example` to `.env`. Everything is env-backed; in Cloud Run the same
keys come from Secret Manager / `--set-env-vars`. `USE_MOCK=true` is the default.

## What's NOT here yet (your lane)

- `tools/aria_tools/` — 9 ARIA tool functions + FastAPI `main.py`
- `tools/pulse_tools/` — 6 PULSE tool functions + FastAPI `main.py`
- `tools/shared/` extras from SPEC-00: `models.py`, `auth.py`, `rate_limit.py`, `logger.py`
- `agents/aria/`, `agents/pulse/` — ADK agent wiring (system prompts already exist)
- `data/schema/`, `data/seed/` — real SQL
- `tests/`
