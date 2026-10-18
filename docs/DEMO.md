# Three-minute ARC demonstration

Updated October 18, 2026 · Matches product specification 1.1.

For the Google-backed local setup, see [LOCAL_GOOGLE.md](LOCAL_GOOGLE.md).
The recording sequence below is the explicit offline fixture scenario.

## Preparation

From the repository root, start a fresh independent scenario:

```bash
.venv/bin/python scripts/run_local.py --offline --data-dir /tmp/arc-recording-01
```

Choose another unused directory for a second take; reusing one retains prior
orders, stock, discounts and approvals. If the usual ports are occupied, add
`--web-port 3100 --aria-port 8101 --pulse-api-port 8102 --pulse-port 8502` and open those URLs.
Do not stop another running demo to free its ports.

Open the store and manager dashboard. Explain upfront that this branch runs
local deterministic orchestration and simulated inventory actions; Google model
and cloud SDK execution are the remaining integration work. The seeded customer
history is synthetic. Do not present the demo login as production authentication.

## Recording sequence

| Time | Show | Explain |
|---|---|---|
| 0:00–0:20 | ARIA and the store | “Sales record what customers bought. ARC preserves what they wanted but couldn't get.” |
| 0:20–0:55 | Request weekly halal groceries with brown rice; choose Temporary compromise; confirm | “A successful checkout can still contain an unresolved customer need.” |
| 0:55–1:35 | PULSE counts and the actual customer statement | Distinguish satisfied alternatives, compromises, rejections, unknown feedback, and labeled synthetic seeds. |
| 1:35–2:05 | Compare transfer, replenishment and defer; approve transfer | Show quantity and source safety stock. State clearly that the transfer is a local simulation. |
| 2:05–2:35 | New shopper requests and buys brown rice | Show that persisted inventory changed; the after-action monitor counts a fulfilled request. |
| 2:35–2:50 | Approve Laban discount; refresh storefront | The manager's decision controls the shopper's actual local price. |
| 2:50–3:00 | Evaluation and integration boundary | Curated synthetic examples demonstrate the distinction; they are not a production accuracy benchmark. |

## Evidence to verify during the take

- The unavailable product was explicitly requested; the session is logged once
  and updated as feedback and checkout arrive.
- The temporary compromise remains visible even after the order succeeds.
- The manager sees your session statement alongside labeled synthetic seeds.
- The transfer changes actual shared local inventory without crossing source
  safety stock. It is not a shipment or supplier delivery.
- A **new** shopper session buys the original product. The monitor counts an
  observed post-decision fulfillment; it does not claim causality.
- Pending discounts are inactive. After approval, the catalog refreshes within
  ten seconds and a new request uses the canonical approved price.
- No fake order or logging fallback masks a stopped backend. A missing/stale quote
  asks for another review instead of ordering an unexpected basket.

## Optional checks and claims

Optional unscripted check: request vegan groceries under AED 20 and inspect the
actual basket. Cancel with “yes but cancel the order” to demonstrate that prefix
matching cannot accidentally place an order.

Do not claim causal revenue recovery, first-of-its-kind technology, an executed
supplier order, or live Gemini reasoning in this branch.

The evaluation comparison is **20/20 local rule matches versus 10/20 for the
acceptance-only baseline** on twenty curated synthetic development examples,
including five compromise cases. It is not a held-out or representative benchmark.
See [EVALUATION.md](EVALUATION.md) before presenting those numbers.

Product behavior: [ARC_SPEC.md](../ARC_SPEC.md). Interfaces:
[AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md). Full setup:
[DEPLOYMENT.md](../DEPLOYMENT.md).

## Shopping navigation checks

- Ask: `Weekly halal groceries, family of 4, AED 300. Include brown rice.`
  Check that the proposed basket includes stocked brown rice and stays within
  AED 300. Seafood does not require a halal slaughter label.
- Open the cart icon to review `/cart`. Change a quantity or remove an item;
  review the updated quote before confirming.
- After confirming, choose **View my orders**, or use **Orders** in the navigation.
  The order should remain visible after refreshing `/orders`.
