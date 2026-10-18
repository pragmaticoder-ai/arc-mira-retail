# ARC API and tool contracts

Updated October 18, 2026 · Specification 1.1

Generated OpenAPI documents describe actual HTTP request models:

- [ARIA agent API](specs/openapi_aria_agent.yaml)
- [PULSE agent API](specs/openapi_pulse_agent.yaml)
- [ARIA tool service](specs/openapi_aria_tools.yaml)
- [PULSE tool service](specs/openapi_pulse_tools.yaml)

Most handlers return plain dictionaries without response models; generated
OpenAPI response bodies are consequently generic. The behavioral response shapes
below and the contract tests supplement those schemas. Python tool functions and
HTTP request models are distinct interfaces; additional Python arguments are not
automatically exposed over HTTP.

## 1. ARIA service

### POST /aria/chat

Local default service: `http://127.0.0.1:8001`. The storefront proxies this through
`POST /api/aria/chat`. All requests include a message; session IDs are generated
when omitted and returned for subsequent calls.

```json
{
  "session_id": "a8a977e1-93a3-4e0f-a2fd-bd313ce497b1",
  "customer_id": "sarah_123",
  "store_id": "dubai_marina_01",
  "message": "Weekly halal groceries, family of 4, AED 300. Include brown rice.",
  "cart": null,
  "quote_id": null,
  "feedback": null,
  "product_id": null
}
```

| Field | Contract |
|---|---|
| session_id | Optional UUID; a session remains bound to customer/store |
| customer_id | Defaults to sarah_123; must resolve to a demo profile |
| store_id | Defaults to dubai_marina_01 |
| message | 1–1000 characters; whitespace-only is rejected |
| cart | Optional list of product/quantity dictionaries; authoritative prices are rebuilt |
| quote_id | Current server quote for confirmation |
| feedback | Optional satisfied / compromise / rejected selection |
| product_id | Original unavailable product being rated; required to disambiguate multiple offers |

Response:

| Field | Shape / meaning |
|---|---|
| session_id | UUID string |
| reply | Shopper-facing response |
| cart | items, total_aed, promotion |
| quote_id | Current quote identifier, or null |
| reasoning | type/text operation summaries; not model-generated thoughts |
| order | null or order_id/status/total_aed/estimated_delivery_window |
| session_logged | Actual successful local logging status |
| demand_signals | Current product-level evidence records |
| substitution_offers | Original product, candidate ID/name, quantity and feedback outcome |
| mode | local_rules |

Each cart line includes product_id, product_name, quantity, price_aed, aisle_ref,
in_stock, discount_active and substituted. A promotion is null or contains
promotion_id, promotion_name, discount_aed and new_total_aed.

### Confirmation protocol

1. Build or sync the basket and retain the returned session_id and quote_id.
2. Send an exact affirmative message with that quote_id. Supported affirmatives:
   confirm, yes, place order, go ahead, proceed, confirm order.
3. Send current browser cart edits with confirmation. If the basket differs, the
   server returns a new quote and no order; review and confirm again.
4. If prices/promotions changed, the server similarly returns a replacement quote.
5. A successful confirmation commits the canonical basket, not a rebuilt demo cart.
   Repeating a confirmed session returns the existing order.

`sync cart` and `review cart` with a cart request a quote without ordering. A new
manual-only basket first goes through quote review. Cancellation phrases or a
message containing cancel/don't place/do not place close an active session without
placing an order. Cancellation does not reverse an already confirmed order.

Feedback accepts the alternative for satisfied/compromise and records the original
need separately; rejected removes a substituted line. Natural-language feedback
uses conservative local rules. Unknown wording is not automatically satisfaction.

### HTTP errors

- 422: Pydantic request validation, including invalid UUIDs or feedback enums.
- 400: invalid profile/cart/constraints, empty basket, canonical price mismatch.
- 409: customer/store conflicts with an existing session.
- 501: chat requested with USE_MOCK=false; ADK execution is deferred.

Missing or stale quotes normally produce a successful review response with no
order rather than a failed checkout. The Next.js proxy returns error_message for
upstream failures and 503 when ARIA is unavailable or its response is malformed.

### GET /aria/inventory

Query: store_id (defaults to dubai_marina_01). Response: `{ "items": [...] }` with
current local inventory rows. The storefront proxy is `GET /api/aria/inventory`.
Approved discount flags and effective-price fields come from shared storage.

### GET /health

ARIA reports local_rules / healthy in local mode and unavailable /
integration_required otherwise. This is not a production dependency check.

## 2. Optional PULSE HTTP service

The launcher does not start this service. The Streamlit dashboard calls PULSE
functions in-process with the same storage environment.

| Method/path | Request | Response |
|---|---|---|
| POST /pulse/analyze | store_id; hours 1–168 (default 48); min_incidents 1–100 (default 5) | stockout_alerts, perishable_alerts, demand_insights, mode=local_rules, estimates label |
| POST /pulse/decision | proposal_key, store_id, action | Persisted demand decision |
| POST /pulse/discount-decision | product_id, store_id, status | Persisted discount decision |
| GET /health | none | Service liveness and legacy mock/live mode label |

Demand action values are transfer/replenish/defer; availability is re-evaluated
server-side. Invalid, expired or conflicting decisions return 409. Discount status
is approved/rejected. Successful identical decisions are idempotent. The PULSE
health endpoint's legacy live label does not establish working Google integration;
`/pulse/analyze` returns 501 when USE_MOCK=false.

The analysis endpoint's legacy stockout cycle requires the default five-incident
threshold for its root-cause tool. Lower thresholds can expose unsupported legacy
error paths. It requests 120-unit PO drafts. The dashboard uses incident/reorder
thresholds; demand replenishment uses explicit unresolved counts/reorder thresholds.
Shared PO deduplication can therefore return a previously created proposal with
its original quantity, evidence and decision state.

## 3. Demand intelligence Python interfaces

```python
demand_insights(store_id, hours=48) -> list[dict]
decide_demand(proposal_key, store_id, action) -> dict
decide_discount(product_id, store_id, status) -> dict
```

Each insight contains product/store identifiers, proposal_key, counts, evidence,
synthetic_sessions, summary, recommended_action, action_options, optional decision
and outcome_monitor. Counts include the six outcomes and explicit unresolved sum.
Evidence includes the original statement, session ID, preserved timestamp, order
flag and data origin. Certainty is explicit/observed/unknown, not a probability.

Action options include availability, quantity, reason and optional source-store or
lead-time context. Transfer/replenish require three explicit unresolved signals;
defer remains available. Transfer also requires source stock above its reorder
threshold. Proposal key: `demand:{store}:{product}:{business_date}`.

A decision includes baseline counts, evidence-session IDs, selected action,
quantity, status=approved, execution label and decision timestamp. Transfer execution
is local_inventory_simulation; replenishment is purchase_order_drafted; defer is
observation_only. A replenishment decision does not approve its separate PO.

Outcome monitoring includes baseline, after counts, after_sessions, collecting /
awaiting_action status and a non-causal interpretation note. Sessions first seen
before the decision do not become post-action samples merely by being updated.

## 4. Tool services

ARIA exposes nine POST tool routes; PULSE exposes six. They remain callable in
local mode and are distinct from the agent-facing routes above. Tool routers use
IAM verification outside development and an explicit development bypass. The
current agent endpoints do not inherit that dependency. Production authorization
and audience policy remain integration work.

| ARIA tool route | Function | Result |
|---|---|---|
| /tools/parse-intent | parse_intent | goal, dietary_preference, optional budget/household, urgency |
| /tools/get-customer-context | get_customer_context | Profile defaults and up to three past orders |
| /tools/build-cart | build_cart | items, total_aed, items_unavailable |
| /tools/check-stock | check_stock | available, quantity, aisle_ref, active discount, alternative stores |
| /tools/suggest-substitution | suggest_substitution | Candidate or null, relevance/price/history metadata and optional gap event |
| /tools/optimize-budget | optimize_budget | updated_cart, new_total_aed, changes_made |
| /tools/apply-promotion | apply_promotion | Applied promotion or no-application result; preview does not consume usage |
| /tools/place-order | place_order | Canonically validated order or standard tool error |
| /tools/log-session | log_session | session_id, logged, operation timestamp |

| PULSE tool route | Function | Result |
|---|---|---|
| /tools/detect-patterns | detect_patterns | patterns with store/window/evidence |
| /tools/find-root-cause | find_root_cause | Heuristic hypothesis, confidence, evidence and recommended_action |
| /tools/predict-stockout | predict_stockout | Synthetic scenario, surfaced flag, fixture confidence and evidence |
| /tools/calculate-impact | calculate_impact | Illustrative lost/at-risk/recoverable figures and assumptions |
| /tools/draft-purchase-order | draft_purchase_order | Existing or new PO, actual persisted status and creation context |
| /tools/execute-perishable-discount | execute_perishable_discount | Perishable proposals with persisted batch-decision status |

Detailed signatures, inputs and validation are in the [individual specifications](specs/README.md).

### Python-only extensions and limits

- `log_session` has keyword-only demand_signals and requested_items. Local ARIA
  calls it directly. The current LogSessionRequest HTTP model does **not** expose
  these fields; sending extra JSON does not persist them. Remote-tool integration
  must explicitly extend that request model before using it for the new workflow.
- `place_order` supports a Python dietary_preference override and idempotency_key.
  The HTTP model exposes only the latter and otherwise uses profile diet. Direct
  tool calls do not require an agent quote ID; quote review belongs to ARIA.
- `apply_promotion` supports Python-only promotion_id selection and record_usage.
  Public HTTP preview requests do not expose those controls. Checkout handles
  durable usage accounting; preview should not be treated as a purchase.
- `optimize_budget` is a standalone heuristic helper, not a mandatory local chat
  step. Canonical inventory validation belongs to quote/checkout.

### Standard tool error

```json
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "error_message": "Human-readable explanation",
  "retry_suggested": false
}
```

Functions return that dictionary. Tool route business errors generally retain HTTP
200; malformed request models use 422, IAM errors use 401 and rate limiting uses
429. ARIA maps tool errors to a shopper-facing HTTP 400. A caller must not equate
HTTP 200 with tool success without checking the body.
