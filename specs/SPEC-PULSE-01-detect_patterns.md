# SPEC-PULSE-01 — detect_patterns

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/pulse_tools/detect_patterns.py](../tools/pulse_tools/detect_patterns.py).

```python
detect_patterns(store_id: str, hours: int=48, min_incidents: int=5) -> dict
```

HTTP request model `DetectPatternsRequest`:

- `store_id: str` (required)
- `hours: int` = `48`
- `min_incidents: int` = `5`

The exact POST route and framework schema are in
[openapi_pulse_tools.yaml](openapi_pulse_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Read unavailable products from the incident bridge, deduplicate product IDs within each session and aggregate by store/window. Rank by illustrative financial exposure and attach first/last times, samples, peak and substitution-acceptance evidence. This stockout aggregate is distinct from explicit unresolved-intent counts.

## 4. Validation and limits

Nonempty store ID; hours 1–168; min_incidents 1–100, default 5. Exclude rows outside the actual current window and future rows. New active sessions do not imply abandonment; older rows retain legacy fallback semantics.

## 5. Response

patterns with product/store, incident_count, period_hours, estimated_revenue_lost_aed, peak_hour, abandonment_count, average_cart_aed, evidence. Financial exposure is modeled, not observed lost sales.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_pulse01*` cases in
  [tests/unit/pulse/test_pulse_tools.py](../tests/unit/pulse/test_pulse_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
