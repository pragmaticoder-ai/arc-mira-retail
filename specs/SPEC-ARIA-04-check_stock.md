# SPEC-ARIA-04 — check_stock

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/aria_tools/check_stock.py](../tools/aria_tools/check_stock.py).

```python
check_stock(product_id: str, store_id: str) -> dict
```

HTTP request model `CheckStockRequest`:

- `product_id: str` (required)
- `store_id: str` (required)

The exact POST route and framework schema are in
[openapi_aria_tools.yaml](openapi_aria_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Read the product at the selected store. Return current stock/aisle and manager-approved discount fields. If unavailable, enumerate up to three other stores with stock.

## 4. Validation and limits

Product and store IDs must be nonempty. NOT_FOUND means the product does not
exist anywhere in the local catalog. If a known product has no row at the selected
store (including an unknown store ID), return unavailable with quantity zero and
any alternative stores. This helper does not independently validate store existence.
Aisle is null when unavailable. discounted_price_aed may contain a proposed price
even when discount_active is false; consumers must check the active flag before
using it as an approved price.

## 5. Response

product_id, available, quantity, aisle_ref, discount_active, discounted_price_aed, alternative_stores (store ID/name, quantity, distance context).

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_aria04*` cases in
  [tests/unit/aria/test_aria_tools.py](../tests/unit/aria/test_aria_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
