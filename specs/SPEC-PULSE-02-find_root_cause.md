# SPEC-PULSE-02 — find_root_cause

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/pulse_tools/find_root_cause.py](../tools/pulse_tools/find_root_cause.py).

```python
find_root_cause(product_id: str, store_id: str, peak_hour: str, incident_count: int, period_hours: int) -> dict
```

HTTP request model `RootCauseRequest`:

- `product_id: str` (required)
- `store_id: str` (required)
- `peak_hour: str` (required)
- `incident_count: int` (required)
- `period_hours: int` (required)

The exact POST route and framework schema are in
[openapi_pulse_tools.yaml](openapi_pulse_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Compare stockout count and peak time to the seeded replenishment schedule. Return a timing/volume/demand hypothesis and supporting inputs. High/Medium/Low are heuristics based on incident count and schedule availability, not calibrated causal confidence.

## 4. Validation and limits

Existing product; peak format HH:MM-HH:MM; at least five incidents; period 1–168 hours. Without a schedule, return unknown/Low. The optional analysis endpoint does not fully support lower incident thresholds through this legacy tool.

## 5. Response

root_cause, confidence_level, explanation, evidence, recommended_action. Data-source strings retain planned BigQuery/AlloyDB names even when local adapters supplied the data; the UI labels the actual local mode.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_pulse02*` cases in
  [tests/unit/pulse/test_pulse_tools.py](../tests/unit/pulse/test_pulse_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
