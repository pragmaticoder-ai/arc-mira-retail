# Three-minute ARC demonstration

Demo URLs, usernames and passwords: [README — Try the hosted demo](../README.md#try-the-hosted-demo).

This script describes the deployed Google-backed demo. ARIA uses Gemini on Vertex AI through Google ADK. Cloud SQL PostgreSQL stores operational state, and BigQuery holds session demand evidence. MIRA Retail is fictional. Purchase-order receipt and store transfers simulate operational execution within the shared demo inventory.

## Preparation

- Open both hosted apps before recording so cold starts do not consume video time.
- Sign into ARIA as Sarah and PULSE as the manager. Select MIRA Dubai Marina in both.
- Inspect current stock and pending actions before recording. Previous approvals persist. Use an actually unavailable product and a valid pending proposal rather than claiming brown rice is unavailable if someone already restocked it.
- Keep the source product name, shopper statement and action result visible. Show the outcome in Action history after clicking approval.

## Recording sequence

| Time | Show | Explain |
|---|---|---|
| 0:00–0:20 | ARIA storefront and catalog | “Sales tell a retailer what sold. ARC also records what the customer wanted but could not get.” |
| 0:20–0:55 | Ask for weekly halal groceries for four under AED 300, including brown rice | Show the real basket total and unavailable-product response. Explain that Gemini proposes while the server validates price, stock, diet and budget. |
| 0:55–1:15 | Choose Temporary compromise on an actual offer, then review and explicitly confirm checkout | “Accepting an alternative this week does not mean the original preference disappeared.” Open My orders to show the confirmed order. |
| 1:15–1:50 | PULSE Unmet demand and customer evidence | Show the shopper's exact statement. Distinguish satisfied alternatives, temporary compromises and rejection. Identify synthetic seed evidence wherever shown. |
| 1:50–2:15 | Review and approve an available transfer, or Approve & restock (demo) | Show quantity, approval feedback and the persisted result in Action history. Explain that stock receipt is a demo simulation and contacts no supplier. |
| 2:15–2:40 | Switch customer or start a fresh shopping session and request the original product | Show that the next interaction reads updated shared stock. A confirmed order containing the original product supplies the fulfillment signal. |
| 2:40–2:50 | PULSE overview and Action history | Show charts and the completed action. A perishable discount, when available and approved, changes the next shopper quote too. |
| 2:50–3:00 | Verification and closing | “ARC preserves the unmet need, supports a reviewed decision, and makes the next shopping interaction reflect it.” State that financial exposure and later outcomes are estimates and observations. |

If the current catalog does not support a suitable substitution, show the explicit rejection/unmet request honestly. Do not fabricate an accepted alternative or repeat an already completed action as if it were pending.

## What demonstrates impact

- A checkout can succeed while the original preference remains unresolved and visible to the manager.
- The manager sees customer evidence rather than treating every accepted alternative as satisfaction.
- Approvals change shared stock or prices. Rejections leave them unchanged. Repeated PO approvals do not duplicate inventory.
- A subsequent shopper can buy the newly available original item. PULSE retains the action and observes recorded outcomes after it.
- Individual customer profiles keep conversations, baskets and orders separate.

The observed hosted smoke test produced 20 basket lines totaling AED 127.62 for one family-of-four request under AED 300 and disclosed unavailable brown rice. This is one recorded result, not a promise of the same basket after stock or prices change, and not a complete nutrition plan.

## Evidence and boundaries

182 Python tests, 12 frontend tests and the Next.js production build passed. Hosted smoke checks covered authentication, customer scoping, the 4,145-product Marina catalog, substitution feedback, checkout, order history, idempotency and Google analysis. See [UI_QA.md](UI_QA.md).

On 20 curated synthetic development examples, the feedback rule parser matched 20/20 labels versus 10/20 for a simple acceptance-only baseline, including all five compromise cases. This illustrates the feedback distinction. It is not a held-out Gemini accuracy benchmark or representative customer study. See [EVALUATION.md](EVALUATION.md).

Supplier integration, production identity and reliable event delivery remain future work. Do not claim actual supplier delivery, measured revenue recovery, causal uplift, production-scale throughput or universal novelty.


Demo video (3 minutes 24 seconds, AI narration): [Watch the closed-loop walkthrough](https://storage.googleapis.com/aria-mira-retail-demo-video-20261018/ARC_Demo.mp4).


## Recorded hosted demonstration

The replacement video is 3:24 and leads with the real Safa Laban stockout → temporary compromise → PO approval → original-product purchase loop. Five scripted demo request sessions provide the stockout threshold; their evidence is generated through the live assistant. PO-2026-0002 receives 10 units. Sarah’s subsequent order MR-2026-14C0 purchases the original multipack for AED 9.95.

The additional price example shows Sarah’s order MR-2026-460C at AED 34.00, the manager’s 25% chicken discount, and Ahmed’s order MR-2026-0941 at AED 28.50. Footage contains full application windows, edited waits, and synchronized synthetic narration. The submitted public URL is unchanged.
