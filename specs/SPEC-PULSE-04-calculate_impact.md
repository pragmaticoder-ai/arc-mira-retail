# SPEC-PULSE-04 — calculate_impact

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/pulse_tools/calculate_impact.py](../tools/pulse_tools/calculate_impact.py).

```python
calculate_impact(product_id: str, store_id: str, incident_count: int, average_cart_aed: float, abandonment_count: int, days_to_next_delivery: int) -> dict
```

HTTP request model `CalculateImpactRequest`:

- `product_id: str` (required)
- `store_id: str` (required)
- `incident_count: int` (required)
- `average_cart_aed: float` (required)
- `abandonment_count: int` (required)
- `days_to_next_delivery: int` (required)

The exact POST route and framework schema are in
[openapi_pulse_tools.yaml](openapi_pulse_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Compute illustrative margin-weighted exposure using incident_count × average_cart_aed × abandonment_rate × 0.15. Project a seven-day scenario from an assumed 48-hour source period; recoverable is capped by at-risk and adjusted for delivery lead. Names retaining revenue_lost do not establish actual lost sales.

## 4. Validation and limits

At least one incident; positive average cart; abandonment 0..incident_count; nonnegative delivery lead. The observation duration is fixed in the formula; selecting a seven-day dashboard window does not recalibrate it. These figures are not the outcome monitor or a measured ROI.

## 5. Response

revenue_lost_aed, revenue_at_risk_aed, revenue_recoverable_aed, calculation_basis, evidence. Preserve exact assumptions and label displayed values as scenario estimates.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_pulse04*` cases in
  [tests/unit/pulse/test_pulse_tools.py](../tests/unit/pulse/test_pulse_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
