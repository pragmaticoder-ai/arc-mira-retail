# SPEC-PULSE-08 — Manager decisions and outcome observation

Updated October 18, 2026 · Specification 1.1 · Implemented local workflow

## 1. Purpose

Persist a human decision before showing success, propagate it to the shopper's
actual local inventory/prices, and distinguish later observations from prior evidence.

## 2. Interfaces

```python
decide_demand(proposal_key, store_id, action) -> dict
decide_discount(product_id, store_id, status) -> dict
get_alloydb().decide_purchase_order(po_id, status) -> dict
```

Demand and discount decisions also have optional PULSE HTTP routes documented in
[openapi_pulse_agent.yaml](openapi_pulse_agent.yaml). PO buttons use the Python
adapter directly; no separate PO-decision HTTP route is implemented.

## 3. Decision lifetimes

- Demand: one store/product/business-day proposal. Same action returns the existing
  decision; a conflicting action or invalid/expired proposal is rejected.
- PO: pending, approved or rejected proposal reused for the same product/store
  within 24 hours. Creation context and actual stored status survive reruns.
- Discount: store/product/expiry batch. Repeating the same status is idempotent;
  changing a decided batch to the opposite status is rejected.

## 4. Write behavior

Transfer validates source safety stock and updates source/destination atomically.
Its execution label is local_inventory_simulation. Replenishment creates a PO draft
and does not add inventory; approving the demand action is not PO approval. Defer
records observation_only. Discount approval writes percentage, effective price and
active flag to the selected store; rejection does not activate it.

The operational transaction protects the decision and its local mutation. No
carrier, supplier or payment is invoked. Failures are displayed, not swallowed.

## 5. Outcome monitor

Store baseline counts, evidence-session IDs and decision time. After counts include
product-request sessions whose preserved first timestamp is later than that time.
An older session that finishes later is not a newly observed post-decision session.

Display baseline, after outcome counts, after_sessions and awaiting_action/collecting
status. Describe these as observations, never proven intervention effects or
realized financial recovery. A confirmed order containing the requested original
is the concrete fulfillment signal.

## 6. Integration boundaries

The storefront and dashboard require identical absolute storage paths in separate
Python processes. The two databases are not one distributed transaction. Cloud
release requires managed storage and reliable event delivery. UI success state
cannot substitute for persisted operational state.

## 7. Verification

[tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py)
covers cross-process visibility, same-action retries, persisted PO state, discount
price changes and outcome counts. [Dashboard tests](../tests/integration/test_dashboard.py)
click the real decision controls and verify refresh behavior.
