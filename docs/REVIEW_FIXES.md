# Review fixes and capability boundaries

Updated October 18, 2026 · Specification 1.1

| Reviewed issue | Change |
|---|---|
| Live Google agent execution is unfinished | Explicitly deferred by scope. Live endpoints return a clear 501; local mode is labeled rules, not Gemini. |
| Storefront invents orders and bridge writes | Removed the scripted response module. Storefront calls ARIA; cart-building, feedback, checkout and cancellation publish local incident rows; quote-only edits do not necessarily republish them. |
| Brown-rice stockout never reaches PULSE | Actual requested unavailable products, explicit feedback and accepted substitutes are retained through checkout. Repeated logging updates one session row. |
| Diet and budget ignored | Parsed constraints override saved defaults; exclusions persist in the session; canonical pricing and budget checks apply to generated and manually edited baskets. |
| Checkout orders a rebuilt basket | Durable session quote and quote ID; changed baskets/prices must be reviewed again. Only exact affirmative messages can confirm. |
| Client controls prices or negative quantities | Canonical inventory prices, positive integer quantities, duplicate-product consolidation, exact promotion eligibility, and atomic stock/order writes. |
| Retries duplicate orders or promo usage | Durable order idempotency; previewing promotions consumes no usage; checkout consumes usage once. |
| PO approval creates another pending PO | Public decision API; approved/rejected proposals survive refresh in the same 24-hour cycle. |
| Discount already active / approval does not cross apps | Seed discount inactive; expiry-batch decisions persist, store-specific inventory and price update atomically; storefront fetches live local inventory. |
| Cart totals freeze after edits | Edits invalidate the quote and promotion; a server quote is required before checkout. |
| API errors render blank messages | Proxy validates responses and forwards useful validation errors; UI checks HTTP status. |
| Reload fabricates a confirmed order | Confirmation requires a stored order; session-local receipt survives refresh. |

## Distinguishing capability

An unavailable request remains linked to customer evidence and the substitute.
Explicit “satisfied”, “compromise” and “rejected” feedback is preserved separately;
ambiguous feedback remains unknown. Cancellation records abandonment. A fulfilled
original request is recorded only after a confirmed order includes that product.
PULSE compares three actions; stock-changing options require at least three
explicit unmet signals in the current window. Transfer quantities preserve source
safety stock. Decisions persist by store/product/business day. Historical evidence
remains visible; the monitor separately counts sessions first observed after the
decision. It does not infer causality or invent financial results.

## Remaining limitations

- Local language handling is a conservative English rule parser with a finite
  product-alias set. Unknown requests prompt clarification. It is not a general
  conversational model or a validated sentiment classifier.
- Google SDK/ADK execution and production adapters remain unimplemented.
- SQLite serves a single-host prototype. Operational state is serialized under
  a write transaction; incidents use a second store. Cross-store atomic commit is
  not guaranteed. A production integration should use a transactional outbox.
- This is a local demo persona, not a production login or payment flow. Do not
  expose the development services publicly as a production retail system.
- Transfers are local inventory simulations. Replenishment creates a draft,
  requires PO review, and never pretends a supplier delivery occurred.
- Synthetic seed inventory, velocity and historical incidents are labeled. The
  revenue formulas are scenario assumptions, not measured losses or recovery.
- Draft PO decisions are reused for 24 hours. Demand action decisions use one
  business-day cycle; newer cycles may require a new manager review.


See [ARC_SPEC.md](../ARC_SPEC.md) for product requirements,
[DATA_MODEL.md](../DATA_MODEL.md) for evidence persistence, and
[the specification index](../specs/README.md) for interface and workflow details.
