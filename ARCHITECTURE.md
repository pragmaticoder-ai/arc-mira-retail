# ARCHITECTURE.md — ARC System Design
> MIRA Retail · Agentic Retail Command

---

## 1. Design principles

1. **Event-driven, not tightly coupled** — ARIA and PULSE are independent agents. The BigQuery incidents table is their only communication channel. Either agent can fail without breaking the other.
2. **Tools drive reasoning** — agents reason through tool docstrings, not hardcoded logic. The quality of reasoning is proportional to the quality of tool descriptions.
3. **Schema-first** — AlloyDB schema is defined before any agent or tool is written. Every tool function is a thin wrapper over a schema query.
4. **Visible reasoning** — the Streamlit UI exposes the full ReAct chain (THOUGHT → ACTION → OBSERVATION) so judges can see the agent thinking, not just the final answer.
5. **Fail gracefully** — every tool function returns a structured error response. Agents handle tool failures by retrying once, then informing the user.

---

## 2. Agent reasoning model (ReAct)

Both ARIA and PULSE use the ReAct loop via Google ADK:

```
User message / dashboard trigger
        │
        ▼
THOUGHT  → Gemini decides what to do next
        │
        ▼
ACTION   → Gemini calls a tool with parameters
        │
        ▼
OBSERVATION → Tool returns structured JSON
        │
        ▼
THOUGHT  → Gemini evaluates observation, decides next step
        │
    (repeat until done)
        │
        ▼
ANSWER   → Final response to user / dashboard
```

**What drives the THOUGHT:** the system prompt defines sequencing rules and decision logic. Gemini generates thoughts consistent with those rules — the thoughts are not templated, they are predicted.

**What drives the ACTION:** tool docstrings define when each tool should be called, what parameters it expects, and what it returns. These descriptions are the reasoning instructions.

---

## 3. ARIA agent design

### 3.1 Responsibility
ARIA handles all customer-facing interactions: intent parsing, cart building, stock resolution, budget optimization, promotion application, order placement, and session logging.

### 3.2 Tool execution sequence (happy path)

```
parse_intent()
      ↓
get_customer_context()
      ↓
build_cart()
      ↓
check_stock() [for each item]
      ↓ [if unavailable]
suggest_substitution()
      ↓
optimize_budget() [if over budget]
      ↓
apply_promotion()
      ↓
[present cart to customer, wait for confirmation]
      ↓
place_order()
      ↓
log_session()  ← ALWAYS last, even if no order placed
```

### 3.3 AlloyDB AI integration
`suggest_substitution()` uses AlloyDB AI's ScaNN vector index for semantic product search:
- Products are embedded at insert time using `google_ml_integration` extension
- Query: cosine similarity between the unavailable product's embedding and all in-stock products
- Filtered by: dietary_flags, price range (±20%), stock_quantity > 0
- Returns: top 1 result with similarity score and plain-language reason

### 3.4 BigQuery bridge write
`log_session()` writes a structured row to `arc_dataset.incidents`. This is the bridge that makes PULSE possible. The write is idempotent (session_id is the primary key). Failed writes retry up to 3 times with exponential backoff.

---

## 4. PULSE agent design

### 4.1 Responsibility
PULSE reads the incidents bridge and surfaces operational intelligence to store managers: stockout patterns, root causes, stockout predictions, and purchase order drafts.

### 4.2 Tool execution sequence

```
detect_patterns()  ← reads BigQuery incidents (last 48 hrs)
      ↓
find_root_cause()  ← cross-references AlloyDB replenishment_schedule
      ↓
predict_stockout() ← BigQuery ML ARIMA_PLUS demand forecast
      ↓
calculate_impact() ← revenue lost + revenue at risk (AED)
      ↓
draft_purchase_order()  ← writes pending PO to AlloyDB
      ↓
[surface to manager dashboard, wait for approval]
```

### 4.3 BigQuery ML integration
`predict_stockout()` uses BigQuery ML's `ARIMA_PLUS` model:
```sql
CREATE OR REPLACE MODEL arc_dataset.demand_forecast
OPTIONS(model_type='ARIMA_PLUS', time_series_timestamp_col='timestamp',
        time_series_data_col='incident_count', time_series_id_col='product_id')
AS SELECT ...
```
Predictions with confidence > 0.7 are surfaced to the manager dashboard.

### 4.4 Manager approval flow
1. PULSE drafts a PO in AlloyDB `purchase_orders` table with `status='pending'`
2. Manager sees the PO card in PULSE dashboard with one-click approve/reject
3. On approval: `status='approved'`, `reviewed_at=NOW()`
4. On rejection: `status='rejected'`, `manager_note=<reason>`
5. All decisions are logged with timestamp for audit

---

## 5. BigQuery bridge design

### 5.1 Why BigQuery, not AlloyDB?
- BigQuery is optimized for analytical queries across millions of rows — pattern detection, aggregation, ML
- AlloyDB is optimized for transactional queries — individual order writes, stock updates
- Using the right tool for the right job: ARIA writes operational transactions to AlloyDB, but logs the analytical signal (session summary, friction points) to BigQuery

### 5.2 Write path (ARIA → BigQuery)
```python
# Triggered at end of every ARIA session
log_session(
    session_id=str(uuid4()),
    customer_id="sarah_123",
    store_id="dubai_marina_01",
    items_unavailable=[{"product_id": "rice_brown_500g", "name": "Brown rice 500g"}],
    ...
)
# → BigQuery streaming insert → arc_dataset.incidents
```

### 5.3 Read path (PULSE ← BigQuery)
```sql
-- detect_patterns() query
SELECT product_id, COUNT(*) as incident_count,
       SUM(cart_total_aed * 0.15) as estimated_revenue_lost,
       MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
FROM arc_dataset.incidents
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
  AND ARRAY_LENGTH(items_unavailable) > 0
GROUP BY product_id
HAVING incident_count >= 5
ORDER BY estimated_revenue_lost DESC
```

---

## 6. AlloyDB AI vector search

`suggest_substitution()` uses AlloyDB AI for semantic product similarity:

```sql
-- Enable extensions (one-time setup)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS google_ml_integration;

-- Add embedding column to inventory
ALTER TABLE inventory ADD COLUMN embedding vector(768);

-- Generate embeddings at insert time
UPDATE inventory
SET embedding = embedding('textembedding-gecko@003',
                          product_name || ' ' || category || ' ' || dietary_flags)
WHERE embedding IS NULL;

-- Create ScaNN index
CREATE INDEX ON inventory
USING scann(embedding cosine)
WITH (num_leaves=10);

-- Semantic substitution query (in suggest_substitution tool)
SELECT product_id, product_name, price_aed,
       1 - (embedding <=> query_embedding) AS similarity
FROM inventory
WHERE store_id = $1
  AND stock_quantity > 0
  AND price_aed <= $2
  AND dietary_flags ILIKE '%' || $3 || '%'
ORDER BY embedding <=> query_embedding
LIMIT 1;
```

---

## 7. Frontend architecture

### 7.1 ARIA customer app (Next.js)

**Why Next.js, not Streamlit:** ARIA must feel like a real ecommerce product, not a data tool. Judges need to see a customer-facing grocery store where ARIA is integrated — not ARIA bolted onto a Streamlit page. The product context (category nav, product grid, store selection) is what makes the ARIA panel credible. Streamlit cannot deliver this without feeling like a prototype.

**Layout:** Three-column layout
- Left column (110px): category sidebar — 8 grocery categories, halal filter, budget slider, store selector
- Center column (fluid): product grid — 6 products per category, in-stock/out-of-stock states, add-to-cart
- Right column (160px): ARIA chat panel — message thread, live cart preview, confirm order button

**Key components:**
- `NavBar` — MIRA Retail logo, search bar, cart icon with item count, user avatar
- `CategorySidebar` — 8 grocery categories, active state, halal filter toggle, budget input
- `ProductGrid` — product cards with image placeholder, name, price, add button, added state
- `AriaPanel` — chat thread, AI/user message bubbles, cart mini-summary, text input + send
- `ReasoningDrawer` — expandable "How did ARIA decide this?" panel showing ReAct chain
- `CartPreview` — live cart within the ARIA panel, item list, total, confirm button

**State management:** React context for cart state, shared between ProductGrid and AriaPanel

**ARIA integration:** ARIA panel calls the ARIA agent Cloud Run endpoint. Cart state updates in real time as ARIA calls `build_cart()` and `place_order()`. Product grid highlights items ARIA has added.

**Tech:** Next.js 14 (App Router), Tailwind CSS, TypeScript

---

### 7.2 PULSE manager dashboard (Streamlit)

**Why Streamlit, not Next.js:** PULSE is a data-heavy operations tool, not a consumer product. Store managers need alert cards, charts, and one-click approvals — exactly what Streamlit is designed for. Looker Studio embeds, auto-refresh, and BigQuery-driven charts are all first-class Streamlit features. No custom frontend framework needed.

**Layout:** Two-section layout within Streamlit's native sidebar + main area
- Sidebar: store selector, date range filter, refresh button, last-updated timestamp
- Main area — top: metric cards (incidents, revenue lost, POs pending), alert cards ranked by AED impact, root cause + evidence panels, PO approve/reject buttons
- Main area — bottom: Looker Studio iframe embeds (stockout trends, promotion effectiveness)

**Key components:**
- `st.metric()` — headline numbers (incidents, AED lost, POs pending)
- Alert cards via `st.container()` — one per stockout pattern, ranked by revenue impact
- Evidence expander via `st.expander()` — shows data sources, row counts, date ranges
- PO approval via `st.button()` — writes to AlloyDB `purchase_orders` on click
- Looker embed via `st.components.v1.iframe()` — promotion effectiveness, stockout trends
- Auto-refresh via `st.rerun()` every 10 seconds — live state change visible during demo

**The before/after demo moment:** dashboard auto-refreshes every 10 seconds. When ARIA logs a session to BigQuery, PULSE detects it within one refresh cycle and the alert card appears on screen — judges see the causal chain live.

---

## 8. Security model

| Concern | Implementation |
|---------|---------------|
| Service-to-service auth | IAM service accounts + Workload Identity |
| Database credentials | Secret Manager (never in code or env files) |
| AlloyDB network | Private IP, Cloud SQL Auth Proxy or AlloyDB connector |
| Cloud Run invocation | Authenticated (IAM) — no public unauthenticated access |
| No secrets in git | `.gitignore` covers `.env`, `*-key.json`, `*.pem` |

---

## 9. Observability

Every tool function logs to Cloud Logging:
```python
import google.cloud.logging
client = google.cloud.logging.Client()
logger = client.logger("arc-tool-functions")

logger.log_struct({
    "agent": "ARIA",
    "tool": "build_cart",
    "customer_id": customer_id,
    "latency_ms": elapsed_ms,
    "items_returned": len(items),
    "status": "success"
})
```

Cloud Monitoring dashboard tracks: request count, p50/p95 latency, error rate per tool function.

---

*MIRA Retail · ARC v1.0 · Architecture v1.0*

---

## 9. Build ownership split

| Component | Owner | Framework |
|-----------|-------|-----------|
| ARIA agent (ADK + system prompt) | Both | Python |
| ARIA tool functions (9) | Partner | Python + Cloud Run |
| PULSE agent (ADK + system prompt) | Both | Python |
| PULSE tool functions (5) | Partner | Python + Cloud Run |
| AlloyDB schema + seed data | Partner | SQL |
| BigQuery bridge + ML model | Partner | SQL + BigQuery ML |
| ARIA customer app | You | Next.js 14 + Tailwind |
| PULSE manager dashboard | Partner | Streamlit |
| GCP infra setup | Partner | gcloud CLI |
| Pitch deck + demo video | You | — |

---

## 10. Winning patterns applied (from Agentic Cinema hackathon analysis)

Four lessons from winning projects applied to ARC:

### 10.1 Lead with a hard cost number
Every winning submission led with a specific, credible loss figure.
ARC's opening statement: **"MIRA Retail loses AED 3,200/month per unresolved stockout product."**
This is MIRA Retail's own operational baseline — use it on pitch slide 1, not buried in PULSE output.

### 10.2 Evidence citations in every PULSE output
Winning projects cited exact sources for every conclusion.
PULSE now returns a mandatory `evidence` block with every finding:
- Data source name (BigQuery incidents, AlloyDB replenishment_schedule)
- Row counts and date ranges used
- Exact formula used for revenue calculations

This makes PULSE feel like an analyst who did real work, not a system that guessed.

### 10.3 Human in the loop — explicit framing
Winning projects made the human decision point explicit and prominent.
ARC's framing: **"PULSE never places an order. It drafts the intelligence and surfaces it to Ahmed. Ahmed approves in one click. The human stays in command."**

PULSE system prompt explicitly states `human_approval_required: True` on every PO.
The Streamlit dashboard shows [Approve] / [Reject] buttons prominently — never auto-approves.

### 10.4 Before/after state change in the demo
Every winning demo showed a visible state change — something broken, then fixed.
ARC demo requirement:

```
BEFORE ARIA logs:    Manager dashboard → no alerts showing
AFTER ARIA logs:     PULSE alert appears within seconds (Streamlit auto-refresh: 10s)
AFTER Ahmed approves: PO status changes pending → approved visibly on screen
```

Streamlit dashboard must auto-refresh every 10 seconds during the demo.
The `st.rerun()` call in `pulse_dashboard.py` handles this.
The state change, shown live, is the single most powerful demo moment.
