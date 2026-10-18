# SPEC-ARIA-07 — apply_promotion

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/aria_tools/apply_promotion.py](../tools/aria_tools/apply_promotion.py).

```python
apply_promotion(cart: list[dict], cart_total_aed: float, dietary_preference: str, store_id: str, session_id: str | None=None, *, promotion_id: str | None=None, record_usage: bool=False) -> dict
```

HTTP request model `ApplyPromotionRequest`:

- `cart: list[dict]` (required)
- `cart_total_aed: float` (required)
- `dietary_preference: str` (required)
- `store_id: str` (required)
- `session_id: str | None` = `None`

The exact POST route and framework schema are in
[openapi_aria_tools.yaml](openapi_aria_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Preview the highest-value eligible promotion, using its category subtotal for percentage/flat discount and overall minimum-cart threshold. Check business date, active state, diet and usage cap. Previewing does not consume usage. Canonical quote/checkout, not this standalone helper, owns authoritative product pricing.

## 4. Validation and limits

Nonempty cart, positive cart_total_aed, supported diet. No eligible promotion is a normal no-application result. A discount cannot reduce the total to zero or below. Python-only promotion_id selects a specific promotion; record_usage is an internal legacy option and is not the durable checkout protocol.

## 5. Response

promotion_applied, promotion_id, promotion_name, discount_aed, new_total_aed, reason. Successful checkout increments persisted usage once; preview must leave usage unchanged.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_aria07*` cases in
  [tests/unit/aria/test_aria_tools.py](../tests/unit/aria/test_aria_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
