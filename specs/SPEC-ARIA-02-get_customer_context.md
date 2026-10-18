# SPEC-ARIA-02 — get_customer_context

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/aria_tools/get_customer_context.py](../tools/aria_tools/get_customer_context.py).

```python
get_customer_context(customer_id: str) -> dict
```

HTTP request model `CustomerContextRequest`:

- `customer_id: str` (required)

The exact POST route and framework schema are in
[openapi_aria_tools.yaml](openapi_aria_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Read the synthetic customer profile and at most three previous orders. Saved defaults are context; supported explicit shopper constraints override them in ARIA.

## 4. Validation and limits

Customer ID is nonempty, at most 100 characters, alphanumeric/underscore. Missing profile returns NOT_FOUND. Validate saved preference, household and budget before returning.

## 5. Response

customer_id, name, dietary_preference, household_size, weekly_budget_aed, preferred_store, last_orders.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_aria02*` cases in
  [tests/unit/aria/test_aria_tools.py](../tests/unit/aria/test_aria_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
