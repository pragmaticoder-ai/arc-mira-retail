# SPEC-PULSE-05 — draft_purchase_order

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google mode uses shared Cloud SQL operational records. Offline tests use explicit memory/SQLite adapters.

## 2. Interfaces

Source: [tools/pulse_tools/draft_purchase_order.py](../tools/pulse_tools/draft_purchase_order.py).

```python
draft_purchase_order(product_id: str, store_id: str, quantity: int, urgency: str, justification: str, revenue_at_risk_aed: float, revenue_recoverable_aed: float, evidence_summary: str) -> dict
```

HTTP request model `DraftPORequest`:

- `product_id: str` (required)
- `store_id: str` (required)
- `quantity: int` (required)
- `urgency: str` (required)
- `justification: str` (required)
- `revenue_at_risk_aed: float` (required)
- `revenue_recoverable_aed: float` (required)
- `evidence_summary: str` (required)

The exact POST route and framework schema are in
[openapi_pulse_tools.yaml](openapi_pulse_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Create a pending local PO or reuse the existing same-product/store PO within 24 hours, including approved/rejected ones. Return its stored quantity, creation evidence and actual decision status. Drafting never sends to a supplier or adds stock.

## 4. Validation and limits

Quantity 1–10000; supported urgency; nonempty justification <=1000 chars; evidence_summary <=500 chars; nonnegative illustrative revenue values; existing product. Public decision operations accept approved/rejected and reject conflicting repeat decisions.

## 5. Response

po_id, product_id, product_name, quantity, urgency, justification, modeled impact, evidence_summary, status, human_approval_required, created_at, optional inventory_received_at and execution. Drafting remains pending. Explicit manager PO approval or demand replenishment approval simulates a one-time delivery in this hackathon demo; see SPEC-PULSE-08. Callers may request different quantities, but deduplication preserves the existing draft.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_pulse05*` cases in
  [tests/unit/pulse/test_pulse_tools.py](../tests/unit/pulse/test_pulse_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.
