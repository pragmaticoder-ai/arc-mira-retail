# SPEC-ARIA-06 — optimize_budget

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/aria_tools/optimize_budget.py](../tools/aria_tools/optimize_budget.py).

```python
optimize_budget(cart: list[dict], target_budget_aed: float, dietary_preference: str='none') -> dict
```

HTTP request model `OptimizeBudgetRequest`:

- `cart: list[dict]` (required)
- `target_budget_aed: float` (required)
- `dietary_preference: str` = `'none'`

The exact POST route and framework schema are in
[openapi_aria_tools.yaml](openapi_aria_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Standalone greedy budget helper: reduce expensive-line quantities and remove lines until the target is met, retaining at least one item. Return each change. The local chat path instead fits generated lines incrementally; it does not automatically call this helper.

## 4. Validation and limits

Nonempty cart, positive target, supported diet; each line needs product ID, quantity >=1 and positive price. Return UNPROCESSABLE when the heuristic cannot reach the target or would fall below 85% of it. This helper is not authoritative inventory repricing or a general essential-item optimizer.

## 5. Response

updated_cart, new_total_aed, changes_made with action/product_name/saving_aed. An already affordable basket returns no changes.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_aria06*` cases in
  [tests/unit/aria/test_aria_tools.py](../tests/unit/aria/test_aria_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
