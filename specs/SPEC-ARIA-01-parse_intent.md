# SPEC-ARIA-01 — parse_intent

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/aria_tools/parse_intent.py](../tools/aria_tools/parse_intent.py).

```python
parse_intent(customer_message: str) -> dict
```

HTTP request model `ParseIntentRequest`:

- `customer_message: str` (required)

The exact POST route and framework schema are in
[openapi_aria_tools.yaml](openapi_aria_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Extract supported English diet, AED/dirham budget, household size and urgency. Preserve the original goal text. Local parsing is deterministic; touching the LLM adapter is not a generation call.

## 4. Validation and limits

Reject empty messages, more than 1000 characters and the implemented disallowed patterns. Recognized budgets must be positive and at most AED 10000. Omitted budget/household remain null. Profile fallback belongs to orchestration.

## 5. Response

goal, dietary_preference, budget_aed (nullable), household_size (nullable), urgency. Diet is halal/vegetarian/vegan/none; urgency is normal/urgent.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_aria01*` cases in
  [tests/unit/aria/test_aria_tools.py](../tests/unit/aria/test_aria_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
