# SPEC-PULSE-03 — predict_stockout

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/pulse_tools/predict_stockout.py](../tools/pulse_tools/predict_stockout.py).

```python
predict_stockout(product_id: str, store_id: str, forecast_days: int=7) -> dict
```

HTTP request model `PredictStockoutRequest`:

- `product_id: str` (required)
- `store_id: str` (required)
- `forecast_days: int` = `7`

The exact POST route and framework schema are in
[openapi_pulse_tools.yaml](openapi_pulse_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

In local mode, calculate a depletion scenario from current store stock and a seeded daily velocity. The forecast adapter is not a trained BigQuery ML model. Its 0.82 confidence fixture is illustrative and must be labeled; the tool suppresses dates when a supplied confidence is below 0.70.

## 4. Validation and limits

Existing product; forecast_days 1–30. The local scenario records horizon context but does not restrict depletion dates to that horizon or prove forecast calibration. Google forecasting remains deferred.

## 5. Response

surfaced, predicted_stockout_date, days_until_stockout, confidence, current_stock, daily_consumption_rate, evidence with synthetic model/velocity/confidence notes. Suppressed dates/day counts are null.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_pulse03*` cases in
  [tests/unit/pulse/test_pulse_tools.py](../tests/unit/pulse/test_pulse_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
