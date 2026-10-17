# ARC — Agentic Retail Command
> AI-powered closed-loop retail intelligence for MIRA Retail

**Team:** Pragmatic Engineers  
**Competition:** AI Builder Cup 2026 — Retail & Commerce Theme  
**Submission deadline:** Sunday, October 18, 2026

---

## What is ARC?

ARC is a two-agent AI system that closes the loop between customer experience and retail operations at MIRA Retail — a modern UAE grocery chain.

**The story in one sentence:**  
*"A customer told ARIA she couldn't find brown rice. The store manager never read that complaint. But he ordered more brown rice anyway — because PULSE read what ARIA wrote."*

### The two agents

| Agent | Role | Audience | Technology |
|-------|------|----------|------------|
| **ARIA** | Customer Experience Agent | Shoppers | Google ADK + Gemini 1.5 Pro |
| **PULSE** | Operations Intelligence Agent | Store Managers | Google ADK + Gemini 1.5 Pro |

### The bridge

A **BigQuery incidents table** that ARIA writes to after every customer session and PULSE reads from to detect patterns. This bridge is the architectural innovation — it makes the two agents a system rather than two separate tools.

---

## Architecture overview

```
Customer chat (Streamlit)          Manager dashboard (Streamlit + Looker)
        │                                        │
        ▼                                        ▼
ARIA — CX Agent                        PULSE — OPS Agent
Google ADK + Gemini 1.5 Pro            Google ADK + Gemini 1.5 Pro
Vertex AI Agent Engine                 Vertex AI Agent Engine
        │                                        │
        ▼                                        ▼
ARIA tool functions (9)                PULSE tool functions (5)
Cloud Run Functions · Python           Cloud Run Functions · Python
        │                                        │
        ▼                                        ▼
AlloyDB for PostgreSQL ←──────────────────────────
(customer_profiles, inventory,
 orders, promotions, purchase_orders)
        │
        ▼
BigQuery bridge ←── ARIA writes ──── PULSE reads ──→
(incidents, inventory_log, promotion_log)
```

---

## Repository structure

```
arc/
├── README.md                    ← you are here
├── ARCHITECTURE.md              ← detailed system design
├── DATA_MODEL.md                ← AlloyDB + BigQuery schemas
├── AGENT_CONTRACTS.md           ← tool function API contracts
├── DEPLOYMENT.md                ← GCP setup + deploy guide
├── CONTRIBUTING.md              ← dev setup + conventions
├── SPEC.md                      ← full product specification
├── .env.example                 ← environment variable template
├── .gitignore
│
├── agents/
│   ├── aria/
│   │   ├── agent.py             ← Google ADK agent definition
│   │   ├── system_prompt.txt    ← ARIA system prompt
│   │   ├── tools.py             ← tool bindings
│   │   ├── main.py              ← Cloud Run entry point
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── pulse/
│       ├── agent.py             ← Google ADK agent definition
│       ├── system_prompt.txt    ← PULSE system prompt
│       ├── tools.py             ← tool bindings
│       ├── main.py              ← Cloud Run entry point
│       ├── Dockerfile
│       └── requirements.txt
│
├── tools/
│   ├── aria_tools/
│   │   ├── __init__.py
│   │   ├── parse_intent.py
│   │   ├── get_customer_context.py
│   │   ├── build_cart.py
│   │   ├── check_stock.py
│   │   ├── suggest_substitution.py
│   │   ├── optimize_budget.py
│   │   ├── apply_promotion.py
│   │   ├── place_order.py
│   │   └── log_session.py
│   ├── pulse_tools/
│   │   ├── __init__.py
│   │   ├── detect_patterns.py
│   │   ├── find_root_cause.py
│   │   ├── predict_stockout.py
│   │   ├── draft_purchase_order.py
│   │   └── calculate_impact.py
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── alloydb_client.py    ← AlloyDB connection + queries
│   │   ├── bigquery_client.py   ← BigQuery client
│   │   └── models.py            ← shared Pydantic models
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── aria-app/                ← Next.js 14 customer ecommerce app
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx         ← main store page
│   │   ├── components/
│   │   │   ├── NavBar.tsx
│   │   │   ├── CategorySidebar.tsx
│   │   │   ├── ProductGrid.tsx
│   │   │   ├── AriaPanel.tsx    ← ARIA chat + live cart
│   │   │   └── ReasoningDrawer.tsx
│   │   ├── context/
│   │   │   └── CartContext.tsx
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── tailwind.config.ts
│   └── pulse-dashboard/         ← Streamlit manager dashboard
│       ├── pulse_dashboard.py
│       ├── components/
│       │   ├── alert_card.py
│       │   └── po_approval.py
│       ├── Dockerfile
│       └── requirements.txt
│
├── data/
│   ├── schema/
│   │   ├── alloydb_schema.sql   ← AlloyDB DDL
│   │   └── bigquery_schema.sql  ← BigQuery DDL
│   └── seed/
│       ├── customer_profiles.sql
│       ├── inventory.sql
│       ├── promotions.sql
│       └── replenishment.sql
│
├── infrastructure/
│   ├── cloudbuild.yaml          ← CI/CD pipeline
│   ├── alloydb_setup.sh         ← AlloyDB cluster + instance
│   └── bigquery_setup.sh        ← BigQuery dataset + tables
│
└── tests/
    ├── test_aria_tools.py
    ├── test_pulse_tools.py
    └── test_bridge.py
```

---

## Quick start

```bash
git clone https://github.com/pragmatic-engineers/arc
cd arc
python -m venv venv && source venv/bin/activate
pip install google-adk google-cloud-bigquery google-cloud-aiplatform \
            google-cloud-alloydb-connector pg8000 streamlit \
            google-cloud-secret-manager pydantic

gcloud auth application-default login
gcloud config set project mira-arc-hackathon

# See DEPLOYMENT.md for full setup
```

---

## Technology stack

| Layer | Technology |
|-------|-----------|
| Agent framework | Google ADK (`google-adk`) |
| LLM | Gemini 1.5 Pro + Gemini 1.5 Flash (Vertex AI) |
| Agent hosting | Vertex AI Agent Engine |
| Tool execution | Cloud Run Functions (Python) |
| Operational DB | AlloyDB for PostgreSQL + AlloyDB AI (ScaNN vector) |
| Analytics bridge | BigQuery + BigQuery ML |
| ARIA frontend | Next.js 14 (App Router, TypeScript, Tailwind CSS) |
| PULSE frontend | Streamlit (Cloud Run) |
| Analytics UI | Looker Studio (embedded in PULSE dashboard) |
| CI/CD | Cloud Build + Artifact Registry |
| Secrets | Secret Manager |
| Monitoring | Cloud Monitoring + Cloud Logging |

---

## Demo script (5 minutes)

| Time | Scene |
|------|-------|
| 0:00–1:30 | Sarah chats with ARIA → cart builds → order placed → stockout logged |
| 1:30–2:00 | BigQuery bridge — one new incident row visible |
| 2:00–3:30 | Ahmed's dashboard → PULSE surfaces pattern → root cause → PO approval |
| 3:30–4:00 | The loop closes — *"tomorrow Sarah finds brown rice in stock"* |
| 4:00–5:00 | Architecture diagram + Phase 2 roadmap |

---

*MIRA Retail · ARC v1.0 · Pragmatic Engineers · AI Builder Cup 2026*
