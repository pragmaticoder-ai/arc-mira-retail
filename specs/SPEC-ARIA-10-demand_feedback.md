# SPEC-ARIA-10 — Explicit demand feedback and reviewed sessions

Updated October 18, 2026 · Specification 1.1 · Implemented local workflow

## 1. Purpose

Preserve the difference between an accepted alternative that satisfies a customer
and one accepted only as a temporary compromise. Keep that difference after an
order succeeds. This is a workflow extension, not a tenth registered ADK tool.

## 2. Interfaces

- `POST /aria/chat`: message, UUID session, optional current cart/quote, explicit
  feedback enum and original product ID.
- `classify_feedback(message)`: conservative local English rules.
- `signal(product, outcome, evidence, substitute_id=None)`: structured evidence.
- `log_session(..., demand_signals=..., requested_items=...)`: direct Python write.

See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) and
[openapi_aria_agent.yaml](openapi_aria_agent.yaml). Google structured extraction
is a future implementation of this boundary, not current execution.

## 3. State transitions

| Event | Outcome / mutation |
|---|---|
| Original requested and unavailable | unknown until a supported explicit statement/selection establishes more |
| Customer accepts and says it meets the need | satisfied; add substitute |
| Customer accepts a temporary replacement | compromise; add substitute; original need remains unresolved |
| Customer declines alternative | rejected; remove a substituted line where applicable |
| Active session cancelled | unresolved signals become abandoned; no order |
| Original product included in a confirmed order | fulfilled with observed order evidence |
| Accepted substitute removed by basket edit | Prior acceptance becomes unknown and requires clarification |

A bare yes does not classify satisfaction. Multiple offers require product-specific
feedback. Manual basket lines supplied with feedback are retained and revalidated.
A product left out for budget is not fulfilled simply because it was available.

## 4. Validation and confirmation

Session IDs are UUIDs and bind customer/store. Validate supported constraints,
canonical quantities/prices and budget. Exact affirmative wording alone does not
order an unreviewed basket: require the current quote ID. Changed manual baskets
and changed prices return a new quote for another review. Repeated confirmation
of an ordered session returns its existing order.

## 5. Evidence and persistence

Store original product, optional alternative, outcome, evidence statement, source
and explicit/observed/unknown certainty. Keep one current product signal per
session; bridge writes update one incident. Unknown is excluded from explicit
unresolved counts. The original session timestamp is preserved across updates.

## 6. Limits

The parser recognizes finite English phrase patterns and product aliases. It is
not a general language model. Browser receipt persistence is separate from durable
backend sessions. Idle timeout detection is not implemented. The two storage
transactions are not a cross-database atomic commit.

## 7. Verification

[tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py)
covers compromise after sale, satisfied/rejected/abandoned outcomes, constraints,
quote edits, stale prices, retries, restarts and manual-item preservation.
The [feedback fixture](../tests/fixtures/demand_feedback.json) and
[evaluation guide](../docs/EVALUATION.md) describe the limited synthetic comparison.
