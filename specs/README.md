# ARC specification index

Updated October 18, 2026 · Specification 1.1

These specifications describe the implemented local prototype. Google SDK
execution and cloud adapters remain deferred. Product-level authority is
[ARC_SPEC.md](../ARC_SPEC.md); interface behavior is in
[AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md).

## Setup

[SPEC-00 — Project setup](SPEC_00_PROJECT_SETUP.md)

## Tools and workflows

| Specification | Scope |
|---|---|
| [SPEC-ARIA-01 — parse_intent](SPEC-ARIA-01-parse_intent.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-ARIA-02 — get_customer_context](SPEC-ARIA-02-get_customer_context.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-ARIA-03 — build_cart](SPEC-ARIA-03-build_cart.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-ARIA-04 — check_stock](SPEC-ARIA-04-check_stock.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-ARIA-05 — suggest_substitution](SPEC-ARIA-05-suggest_substitution.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-ARIA-06 — optimize_budget](SPEC-ARIA-06-optimize_budget.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-ARIA-07 — apply_promotion](SPEC-ARIA-07-apply_promotion.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-ARIA-08 — place_order](SPEC-ARIA-08-place_order.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-ARIA-09 — log_session](SPEC-ARIA-09-log_session.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-ARIA-10 — Explicit demand feedback and reviewed sessions](SPEC-ARIA-10-demand_feedback.md) | Local workflow extension; not an added ADK binding |
| [SPEC-PULSE-01 — detect_patterns](SPEC-PULSE-01-detect_patterns.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-PULSE-02 — find_root_cause](SPEC-PULSE-02-find_root_cause.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-PULSE-03 — predict_stockout](SPEC-PULSE-03-predict_stockout.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-PULSE-04 — calculate_impact](SPEC-PULSE-04-calculate_impact.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-PULSE-05 — draft_purchase_order](SPEC-PULSE-05-draft_purchase_order.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-PULSE-06 — execute_perishable_discount](SPEC-PULSE-06-execute_perishable_discount.md) | Existing tool; Python and HTTP boundaries documented |
| [SPEC-PULSE-07 — Unmet demand and action comparison](SPEC-PULSE-07-demand_intelligence.md) | Local workflow extension; not an added ADK binding |
| [SPEC-PULSE-08 — Manager decisions and outcome observation](SPEC-PULSE-08-manager_decisions.md) | Local workflow extension; not an added ADK binding |

## HTTP snapshots

- [ARIA agent](openapi_aria_agent.yaml): chat, inventory and health.
- [PULSE agent](openapi_pulse_agent.yaml): analysis, demand/discount decisions and health.
- [ARIA tools](openapi_aria_tools.yaml): nine tool routes and health.
- [PULSE tools](openapi_pulse_tools.yaml): six tool routes and health.

Snapshots come from each FastAPI application's `app.openapi()`, retaining runtime
versions and actual request models. Generic dictionary responses and business
error semantics require the prose contracts as well. Regenerate from the app
after changing an HTTP model; do not add Python-only parameters to these schemas
unless the actual request model and handler are extended.

## Verification and presentation

- [Evaluation](../docs/EVALUATION.md): curated synthetic fixture and its limits.
- [Three-minute demo](../docs/DEMO.md): evidence → action → subsequent observation.
- [Review fixes](../docs/REVIEW_FIXES.md): reviewed defects, changes and remaining boundaries.
- [Deployment](../DEPLOYMENT.md): reproducible local launch and planned cloud work.
