# SPEC-PULSE-06 — execute_perishable_discount

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/pulse_tools/execute_perishable_discount.py](../tools/pulse_tools/execute_perishable_discount.py).

```python
execute_perishable_discount(store_id: str) -> dict
```

HTTP request model `PerishableDiscountRequest`:

- `store_id: str` (required)

The exact POST route and framework schema are in
[openapi_pulse_tools.yaml](openapi_pulse_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Propose discounts for stocked perishables when days-to-expiry × seeded daily sales rate is below stock. Tiers: 3 days→15%, 2→25%, 1→40%. Return expiry-batch decision status. For an approved batch, retain its recorded percentage and price instead of presenting a new tier as already approved. Detection does not activate a discount; decide_discount is the manager write path.

## 4. Validation and limits

Nonempty store; perishable with positive stock and 1–3 days to expiry. Expired/day-zero/out-of-range items do not trigger this proposal. Existing inventory expiry is not refreshed each day. Unknown inventory may yield an empty alert list rather than NOT_FOUND.

## 5. Response

perishable_alerts with stock, expiry, velocity assumptions, projected unsold units, proposed percentage/price, illustrative financial values, evidence, status, human_approval_required. Approval is scoped to store/product/expiry batch and changes canonical price.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_pulse06*` cases in
  [tests/unit/pulse/test_pulse_tools.py](../tests/unit/pulse/test_pulse_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
