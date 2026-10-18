# ARC screen inventory — current implementation

Updated October 18, 2026 · Specification 1.1

[BRAND.md](BRAND.md) remains the visual token/design reference. This document
supersedes its older generated-layout assumptions where they conflict with the
implemented workflow. The static mira-screens.html is a visual concept, not a
live demonstration or a source of product/API behavior.

## ARIA storefront

| Route / surface | Current behavior |
|---|---|
| /login | Demo entry form; submitting routes to the store. No authentication, account creation or password reset is implemented. |
| / | Store navigation, responsive product grid, desktop category filters, always-expanded ARIA panel and shared cart |
| /order/confirmed | Requires an actual stored order; shows canonical order total, promotion, delivery estimate and local-prototype note |

There is no /shop route, minimized ARIA tab, separate order-history screen or
checkout payment page. Navigation search and several header links remain presentational;
they are not implemented product features. A cart count reflects shared cart state.

### Catalog and cart

The grid fetches the selected store's current local inventory and refreshes every
ten seconds. Product states include available, unavailable, in-basket and approved
discount. Unavailable products cannot be added through the grid. In-basket products
can be incremented within displayed stock; quantity and price are revalidated by
the server. Category, halal and maximum-product-price filters are browsing filters,
not a replacement for the conversational basket budget.

Editing the basket invalidates the quote and preview promotion. The CTA becomes
**Review updated basket**. A returned server quote must be reviewed before
**Confirm order** can place it. Changing store resets the basket and ARIA session.
On small screens the category sidebar is hidden and the layout stacks vertically.

### ARIA conversation

The panel is labeled **Local rules · shared store inventory**. The initial demo
suggestion explicitly requests brown rice, rather than inventing a stockout for
every shopping session. The panel displays request progress, replies, operation
summaries, explicit substitution feedback and live cart preview.

For each unavailable original product:

- **Meets my needs** accepts the alternative and records satisfied.
- **Temporary compromise** accepts it while preserving an unresolved preference.
- **Decline** records rejection and removes a substituted line where applicable.
- Unrecognized feedback remains unknown. Multiple offers require product-specific
  feedback, rather than attributing one statement to every product.

Operation summaries can be expanded. Their ACTION/OBSERVATION labels describe
local validation and persistence, not a live model's reasoning. Network and
validation errors appear as messages rather than blank assistant bubbles.

### Receipt

The receipt requires a returned order. Browser session storage restores a local
receipt on refresh; a direct visit without an order shows **No confirmed order**.
**Continue shopping** clears the receipt/cart for a new shopper session. The total
is an order total, not proof of payment. Delivery is a future local estimate.

## PULSE dashboard

There is one Streamlit manager workspace, without a manager login. It contains:

1. Store and period selectors, manual refresh and timed fragment refresh.
2. Metrics for stockout sessions, explicit unmet needs, temporary compromises and
   pending purchase orders.
3. **The demand a completed sale can hide**: per-product outcomes, customer evidence,
   synthetic-session labels, action comparison, manager decision and later outcomes.
4. Stockout patterns, operational hypotheses, labeled financial assumptions and
   persisted PO approval/rejection.
5. Perishable discount proposals, batch-specific decisions and approval-controlled
   local shopper prices.

Actions and evidence are shown in the same workspace, not separate detail routes.
Transfer is visibly a local inventory simulation; replenish creates a draft; defer
keeps observation active. Success is shown only after a persisted write. A process
memory warning appears when shared storage is not configured. A local rules label
and synthetic data/estimate notes remain visible.

The outcome monitor reports new request sessions first observed after a decision.
It never labels those counts as proven causal revenue recovery. Approved/rejected
POs survive reruns within the current deduplication cycle.

## Deferred surfaces

Production customer/manager authentication, account management, payment, order
history, supplier submission, logistics tracking and model-backed conversation
are future integration work. Do not include them as working screens in the demo.
