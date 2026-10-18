> Runtime update: [Google-backed local execution](docs/LOCAL_GOOGLE.md) describes
> the implemented Google path and its current boundaries. Older offline sections
> below require explicit `USE_MOCK=true` / `--offline`.

# ARC — Agentic Retail Command

## Product specification 1.1

Updated: October 18, 2026 · Team: Pragmatic Engineers · Theme: Retail & Commerce

This specification describes the local prototype on `feature/unmet-demand-loop`.
It supersedes the original 1.0 design. Google SDK execution and cloud adapters
remain planned work; installing the dependencies or setting `USE_MOCK=false`
does not enable them. Specification version 1.1 does not change package versions.

## 1. Product proposition

**ARC distinguishes satisfied purchases from reluctant substitutions, so retailers
can respond to demand their sales records obscure.**

A customer who buys pasta after asking for unavailable rice has completed a sale.
That sale alone does not establish that the original need was satisfied. ARC
preserves the request, alternative, explicit feedback and subsequent outcome.
The store manager can inspect that evidence before choosing an operational action.

The contribution is an evidence-preserving workflow, not a claim of a novel
forecasting algorithm or a first-of-its-kind retail assistant. Business value is
a hypothesis to evaluate; revenue recovery has not been measured.

## 2. Users and responsibilities

| Surface | User | Responsibility |
|---|---|---|
| ARIA / Next.js storefront | Shopper using a synthetic demo profile | Build a constrained basket, review alternatives, express satisfaction or compromise, and confirm a quote |
| PULSE / Streamlit dashboard | Store manager | Inspect original intent, compare actions, approve/reject proposals and observe later requests |
| Local operational store | Both applications | Persist inventory, session quotes, orders, purchase orders and decisions |
| Incident bridge | ARIA writes; PULSE reads | Maintain one evolving record per customer session, including customer evidence |

## 3. Implemented scope and integration boundary

| Capability | Current implementation | Planned integration |
|---|---|---|
| Intent and feedback interpretation | Conservative English rules, explicit feedback buttons, finite product aliases | Google model producing validated structured output |
| Product similarity | TF-IDF cosine search over current local inventory | Google embeddings and database vector search |
| Conversation execution | Stateful Python orchestration | ADK Runner and durable model sessions |
| Operational storage | SQLite with transactional state snapshot; memory for isolated tests | AlloyDB with normalized transactions |
| Incident analytics | SQLite upserts and Python aggregation | BigQuery with a delivery/idempotency strategy |
| Stockout forecast | Synthetic depletion scenario and illustrative confidence fixture | Evaluated forecasting model |
| Inventory transfer | Manager-approved local stock simulation | Logistics/ERP integration and delivery acknowledgement |
| Replenishment | Persistent PO draft and manager decision | Supplier submission and delivery reconciliation |
| Deployment | One-host local launcher | Cloud Run/Firebase and shared managed storage |

A successful local order is not a payment transaction. `/login` is a demo entry
screen, not an authentication service. No manager login is implemented.

## 4. Core journey

1. A shopper requests weekly halal groceries under AED 300 and includes brown rice.
2. ARIA applies explicit constraints over profile defaults, reads store inventory,
   prices a basket and identifies the requested unavailable product.
3. ARIA offers an alternative without adding it until the customer accepts it.
4. The customer selects **Meets my needs**, **Temporary compromise** or **Decline**.
   Unrecognized wording remains unknown; a bare “yes” is not satisfaction evidence.
5. ARIA keeps the original need and evidence through checkout. Changed baskets or
   prices require a new quote review. Confirmation consumes the current quote.
6. PULSE distinguishes explicit unmet demand from satisfied alternatives and
   exposes the statements behind its counts.
7. The manager compares transfer, replenish and defer. An approved local transfer
   changes shared inventory while preserving the source store's safety stock.
8. A new shopper requests the original product and confirms an order containing it.
   The monitor counts this observed fulfillment after the decision.
9. Separately, a manager-approved perishable discount changes the next shopper's
   catalog and canonical price. Pending discounts are not active offers.

The three-minute presentation is specified in [docs/DEMO.md](docs/DEMO.md).

## 5. Functional requirements

### ARIA

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-ARIA-01 | Parse supported intent and validate profile context | Explicit diet/budget override saved defaults; unknown requests prompt clarification |
| FR-ARIA-02 | Enforce supported exclusions | Excluded product IDs/categories persist for the session and apply to manual edits |
| FR-ARIA-03 | Build within budget | No first-item exception; an unaffordable request may yield an empty basket |
| FR-ARIA-04 | Read current store inventory | Availability and approved prices come from the operational adapter |
| FR-ARIA-05 | Offer alternatives | Dietary constraints and caller price ceiling remain hard gates; broader preferences influence ranking |
| FR-ARIA-06 | Preserve customer feedback | Original product, alternative, outcome, statement and evidence source survive checkout |
| FR-ARIA-07 | Quote authoritatively | Validate positive integer quantities, consolidate duplicates, use inventory prices and eligible promotions |
| FR-ARIA-08 | Require reviewed confirmation | Exact affirmative message plus current quote ID; edited basket/prices require another review |
| FR-ARIA-09 | Commit safely | Atomic operational stock/order write; durable session retry returns the same order |
| FR-ARIA-10 | Record lifecycle | Active, completed and abandoned sessions upsert one incident; cancellation never places an order |
| FR-ARIA-11 | Report failures truthfully | HTTP errors display actionable text; session_logged reflects the actual local logging result |
| FR-ARIA-12 | Show valid receipts | A receipt requires a stored order; refresh restores a session-local receipt, not a fabricated default |

The standalone `optimize_budget` tool remains available. Local chat orchestration
fits a basket incrementally and does not claim to execute all nine legacy tools
on every message. Returned `reasoning` steps are local operation summaries, not
model-generated thoughts.

### Demand evidence

| Outcome | Meaning | Included in explicit unresolved count? |
|---|---|---|
| satisfied | Customer explicitly says the alternative meets the need | No |
| compromise | Customer explicitly accepts a temporary alternative while retaining the original preference | Yes |
| rejected | Customer explicitly declines the alternative | Yes |
| abandoned | Customer cancels with a still-unresolved original need | Yes |
| fulfilled | Confirmed order contains the explicitly requested original product | No |
| unknown | Outcome is not established | No |

At most one current signal per product/session is aggregated. Customer acceptance
alone is not evidence of satisfaction. A product excluded by budget is not recorded
as fulfilled. Removing a previously accepted substitute from an edited basket
invalidates that prior acceptance classification.

### PULSE

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-PULSE-01 | Detect repeated stockouts | Store/window-specific counts; default threshold five incidents |
| FR-PULSE-02 | Separate unmet-intent outcomes | Explicit unresolved = compromise + rejected + abandoned; unknown excluded |
| FR-PULSE-03 | Expose evidence | Session ID, timestamp, statement, source and synthetic-origin label are inspectable |
| FR-PULSE-04 | Compare actions | Transfer/replenish/defer include availability, quantities and tradeoffs |
| FR-PULSE-05 | Require adequate explicit signals | Stock-changing action options require at least three explicit unresolved signals |
| FR-PULSE-06 | Protect source inventory | Transfer cannot reduce source stock below its reorder threshold |
| FR-PULSE-07 | Persist decisions | Store/product/business-day demand proposal key; repeated same decision is idempotent; conflicting decision rejected |
| FR-PULSE-08 | Preserve PO decisions | Pending/approved/rejected PO reused for the same product/store within a rolling 24-hour cycle |
| FR-PULSE-09 | Gate discounts | Approval/rejection scoped to store/product/expiry batch; approval changes the actual local price |
| FR-PULSE-10 | Monitor outcomes | Baseline counts and later product-request sessions displayed separately, without causal claims |
| FR-PULSE-11 | Keep estimates distinct | Hypotheses, synthetic forecasts and modeled financial figures visibly labeled |

Demand replenishment approval creates a PO draft; PO approval is a separate step.
Neither event pretends a supplier delivery occurred. The legacy analysis endpoint
and dashboard assembly are separate callers; their PO quantity policies differ.
See [AGENT_CONTRACTS.md](AGENT_CONTRACTS.md).

## 6. Reliability and operating constraints

- Session IDs are UUIDs and remain bound to their customer and store. Start a new
  session when changing either identity.
- Operational writes serialize within an adapter transaction. SQLite's write lock
  protects checkout across processes. Failed operational writes roll back together.
- Incident and operational databases are separate files. Cross-store atomic commit
  is not guaranteed. A transactional outbox is required for the production design.
- Previewing promotions consumes no usage. Successful checkout consumes usage once.
- Source-local business dates use Asia/Dubai; `DEMO_DATE` overrides business-date
  calculations, not wall-clock timestamps.
- Storefront inventory refreshes every ten seconds. PULSE uses a timed Streamlit
  fragment; the cadence is configurable. This is a refresh policy, not a latency SLA.
- Local services bind to loopback. Production authentication, authorization,
  audience validation and cloud identity integration remain release requirements.
- SQLite snapshots support one-host demonstrations; independent cloud instances
  cannot share these local files. No cloud scalability claim has been validated.

## 7. Evaluation and acceptance

Functional acceptance covers constrained carts, quote review, forged-price and
negative-quantity rejection, duplicate-product stock checks, concurrent checkout,
rollback, retries, process restarts, separate-process visibility, persistent
manager decisions, subsequent fulfillment and dashboard button interactions.

The feedback fixture has 20 curated synthetic English cases. It demonstrates a
representational distinction, not general language accuracy. See
[docs/EVALUATION.md](docs/EVALUATION.md) for the measured comparison and limitations.
Performance targets, real retail uplift and causal revenue recovery remain
unmeasured. Use independently annotated held-out conversations and a controlled
business evaluation before making those claims.

## 8. Documentation map

- [ARCHITECTURE.md](ARCHITECTURE.md): execution paths, state and future cloud boundaries.
- [DATA_MODEL.md](DATA_MODEL.md): local schema, lifecycle and planned data mapping.
- [AGENT_CONTRACTS.md](AGENT_CONTRACTS.md): actual agent/tool HTTP and Python contracts.
- [DEPLOYMENT.md](DEPLOYMENT.md): supported launch procedure and deferred cloud rollout.
- [CONTRIBUTING.md](CONTRIBUTING.md): setup, checks and documentation maintenance.
- [specs/README.md](specs/README.md): individual tool and new workflow specifications.
- [docs/REVIEW_FIXES.md](docs/REVIEW_FIXES.md): issue-to-change traceability and limitations.
