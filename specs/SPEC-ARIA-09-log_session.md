# SPEC-ARIA-09 — log_session

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/aria_tools/log_session.py](../tools/aria_tools/log_session.py).

```python
log_session(session_id: str, customer_id: str, store_id: str, items_ordered: list[dict], items_unavailable: list[dict], substitutions: list[dict], promotion_id: str | None, promotion_saving_aed: float, cart_total_aed: float, budget_aed: float | None, sentiment: str, order_placed: bool, abandonment_reason: str | None=None, *, demand_signals: list[dict] | None=None, requested_items: list[str] | None=None) -> dict
```

HTTP request model `LogSessionRequest`:

- `session_id: str` (required)
- `customer_id: str` (required)
- `store_id: str` (required)
- `items_ordered: list[dict]` = `[]`
- `items_unavailable: list[dict]` = `[]`
- `substitutions: list[dict]` = `[]`
- `promotion_id: str | None` = `None`
- `promotion_saving_aed: float` = `0.0`
- `cart_total_aed: float` = `0.0`
- `budget_aed: float | None` = `None`
- `sentiment: str` = `'neutral'`
- `order_placed: bool` = `False`
- `abandonment_reason: str | None` = `None`

The exact POST route and framework schema are in
[openapi_aria_tools.yaml](openapi_aria_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Upsert one evolving incident per session during shopping, feedback, checkout and cancellation. Preserve original requested products, unavailable products, explicit outcomes and accepted substitutes after a successful sale. Repeated writes update rather than duplicate the session and preserve its original event timestamp.

## 4. Validation and limits

Valid session UUID; allowed sentiment; nonnegative savings/cart/budget; valid product/outcome for demand signals. Empty product arrays and no-order sessions are permitted. Active is not abandoned: order gives completed; an abandonment reason gives abandoned; otherwise active.

## 5. Response

session_id, logged, operation timestamp. Python keyword-only demand_signals and requested_items are used by ARIA directly. The current HTTP LogSessionRequest does not expose those fields; remote integration must extend it explicitly.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_aria09*` cases in
  [tests/unit/aria/test_aria_tools.py](../tests/unit/aria/test_aria_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
