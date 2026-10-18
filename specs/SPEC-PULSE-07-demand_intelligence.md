# SPEC-PULSE-07 — Unmet demand and action comparison

Updated October 18, 2026 · Specification 1.1 · Implemented local workflow

## 1. Purpose

Expose demand that a completed sale can hide and give the manager reviewable
alternatives. This extends the six original PULSE tools without adding an ADK
binding or claiming live model reasoning.

## 2. Interface

```python
demand_insights(store_id: str, hours: int = 48) -> list[dict]
```

The dashboard calls this directly. The optional `/pulse/analyze` response also
includes demand_insights. Source:
[tools/pulse_tools/demand_intelligence.py](../tools/pulse_tools/demand_intelligence.py).

## 3. Aggregation

Filter incidents by store and the current window. Deduplicate signals by original
product within each session. Count satisfied, compromise, rejected, abandoned,
fulfilled and unknown separately. Explicit unresolved is compromise + rejected +
abandoned. Acceptance without a clear statement does not count as satisfaction.

Attach statements, original timestamps, session IDs, order flags and origin
labels. Synthetic seeds remain distinguishable from current local customer rows.
Do not describe explicit request counts as observed lost units or sales revenue.

## 4. Action policy

| Action | Availability | Quantity / tradeoff |
|---|---|---|
| transfer | At least three explicit unresolved signals and a source with spare stock | Cap at source stock above reorder threshold; local simulation |
| replenish | At least three explicit unresolved signals | Max of unresolved count and product reorder threshold; creates PO draft |
| defer | Always | No inventory mutation; collect further evidence |

Prefer transfer when available, otherwise replenish at the threshold, otherwise
defer. Source choices rank by spare stock. Re-evaluate availability at approval;
a proposal is not a reservation or a guarantee of shipping time.

## 5. Response

Each insight has product/store IDs, proposal_key, counts, evidence,
synthetic_sessions, summary, recommended_action, action_options, optional decision
and outcome_monitor. Proposal keys are store/product/business-date scoped.

## 6. Limits

Hours must be 1–168. Quantity policy is a local heuristic; there is no transportation
cost optimizer, supplier API or calibrated demand model. Financial estimates are
separate legacy scenarios and are not used to assert recovered revenue.

## 7. Verification

[tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py)
checks preservation after sale, signal separation, source-safe transfer and later
original-product fulfillment. Dashboard behavior is exercised by
[tests/integration/test_dashboard.py](../tests/integration/test_dashboard.py).
