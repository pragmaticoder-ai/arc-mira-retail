# SPEC-ARIA-03 — build_cart

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/aria_tools/build_cart.py](../tools/aria_tools/build_cart.py).

```python
build_cart(goal: str, dietary_preference: str, budget_aed: float, household_size: int, store_id: str) -> dict
```

HTTP request model `BuildCartRequest`:

- `goal: str` (required)
- `dietary_preference: str` (required)
- `budget_aed: float` (required)
- `household_size: int` (required)
- `store_id: str` (required)

The exact POST route and framework schema are in
[openapi_aria_tools.yaml](openapi_aria_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Classify the goal into supported categories using local rules. Choose a dietary-compatible representative in-stock product per category. Quantity uses a household multiplier: 1 for up to two people, 2 for up to four, 3 above four. Never make a first-item exception to the budget.

## 4. Validation and limits

Nonempty goal up to 500 characters; supported diet; budget in (0, 10000]; household 1–20; store inventory must exist. A line must have enough stock for the household quantity and fit the running budget. An unaffordable basket can be empty.

## 5. Response

items, total_aed, items_unavailable. The helper lists a category product as unavailable only when no category candidate has sufficient stock. ARIA separately preserves explicitly requested unavailable originals; it does not fabricate a brown-rice incident.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_aria03*` cases in
  [tests/unit/aria/test_aria_tools.py](../tests/unit/aria/test_aria_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
