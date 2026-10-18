# SPEC-ARIA-08 — place_order

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/aria_tools/place_order.py](../tools/aria_tools/place_order.py).

```python
place_order(customer_id: str, store_id: str, cart: list[dict], promotion_id: str | None, total_aed: float, idempotency_key: str | None=None, dietary_preference: str | None=None) -> dict
```

HTTP request model `PlaceOrderRequest`:

- `customer_id: str` (required)
- `store_id: str` (required)
- `cart: list[dict]` (required)
- `promotion_id: str | None` = `None`
- `total_aed: float` (required; positive and finite via `Field(gt=0, allow_inf_nan=False)`)
- `idempotency_key: str | None` = `None`

The exact POST route and framework schema are in
[openapi_aria_tools.yaml](openapi_aria_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Within one operational transaction, validate the basket, consolidate duplicate products, reprice from current store inventory, re-evaluate the selected promotion, check the submitted total, reserve stock, consume usage and insert an order. The agent-facing quote review is a separate orchestration requirement; direct tool calls do not carry a quote ID.

## 4. Validation and limits

Existing customer; finite positive total; positive integer quantities; store product and sufficient combined stock; profile or explicit Python diet; exact canonical quoted total. Negative/fractional/bool quantities and forged discounts must not mutate stock. Repeated session-key checkout returns its durable existing order; callers without a key get a 60-second duplicate window.

## 5. Response

order_id, status=confirmed, total_aed, estimated_delivery_window. The result is a local order, not payment or delivery execution. Python dietary_preference override is not exposed by the HTTP request model.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_aria08*` cases in
  [tests/unit/aria/test_aria_tools.py](../tests/unit/aria/test_aria_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
