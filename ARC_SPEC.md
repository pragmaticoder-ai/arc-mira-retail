# ARC — Agentic Retail Command
## Product Specification v1.0
### AI Builder Cup 2026 | Retail & Commerce Theme
**Team:** Pragmatic Engineers  
**Deadline:** Sunday, October 18, 2026  
**Status:** Draft v1.0

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Solution Overview](#3-solution-overview)
4. [System Architecture](#4-system-architecture)
5. [Technology Stack](#5-technology-stack)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Data Model](#8-data-model)
9. [Agent Specifications](#9-agent-specifications)
10. [API Contracts](#10-api-contracts)
11. [Frontend Specification](#11-frontend-specification)
12. [Infrastructure & Deployment](#12-infrastructure--deployment)
13. [Project Setup](#13-project-setup)
14. [Build Plan](#14-build-plan)
15. [Demo Script](#15-demo-script)
16. [Success Criteria](#16-success-criteria)

---

## 1. Executive Summary

**ARC (Agentic Retail Command)** is a two-agent AI system that closes the loop between customer experience and retail operations. A single customer interaction with ARIA (the CX agent) automatically surfaces as operational intelligence in PULSE (the OPS agent) — without any human manually connecting the two.

**The innovation:** A BigQuery bridge that turns customer friction into store commands in real time.

**The story in one sentence:**  
*"Sarah told ARIA she couldn't find brown rice. Ahmed never read that complaint. But he ordered more brown rice anyway — because PULSE read what ARIA wrote."*

---

## 2. Problem Statement

### 2.1 The Gap
MIRA Retail, like most grocery chains, operates with two completely disconnected systems:

- **Customer-facing systems** capture interactions but discard the operational signal (stockouts, substitutions, abandoned carts)
- **Operations systems** rely on weekly reports, manual ticket reviews, and manager intuition — all too slow to prevent revenue loss

### 2.2 The Cost
- A stockout complaint disappears into a support ticket
- The manager sees it on Friday; the damage happened on Tuesday
- Revenue is lost, customers churn, and the problem repeats next week

### 2.3 What's Missing
An autonomous system that:
1. Resolves customer friction in real time
2. Converts that friction into operational intelligence automatically
3. Recommends corrective action before the next customer encounters the same problem

---

## 3. Solution Overview

### 3.1 Product Name
**ARC — Agentic Retail Command**

### 3.2 Tagline
*"From customer chat to store command — one intelligent loop"*

### 3.3 The Two Agents

| Agent | Name | Role | Audience |
|-------|------|------|----------|
| CX Agent | **ARIA** | Customer Experience | Shoppers |
| OPS Agent | **PULSE** | Operations Intelligence | Store Managers |

### 3.4 The Bridge
A **BigQuery incidents table** that ARIA writes to after every session and PULSE reads from to detect patterns. This bridge is the architectural innovation — it makes the two agents a system rather than two separate tools.

### 3.5 The Complete Journey

```
Customer chats with ARIA
        ↓
ARIA builds cart, resolves issues, places order
        ↓
ARIA logs session + friction points → BigQuery Bridge
        ↓
PULSE detects patterns from logged incidents
        ↓
PULSE surfaces root cause + draft PO to manager
        ↓
Manager approves in one click
        ↓
Tomorrow's customer finds the shelf stocked
```

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CUSTOMER INTERFACE                       │
│                   Streamlit Chat UI                          │
│              (Cloud Run — Frontend Service)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  ARIA — CX AGENT                             │
│           Google ADK + Gemini 1.5 Pro                       │
│            (Vertex AI Agent Engine)                          │
│                                                              │
│  Tools (Cloud Run Functions):                                │
│  ├── parse_intent()                                          │
│  ├── get_customer_context()    ──▶ AlloyDB                   │
│  ├── build_cart()              ──▶ AlloyDB + BigQuery        │
│  ├── check_stock()             ──▶ AlloyDB                   │
│  ├── suggest_substitution()    ──▶ AlloyDB AI Vector Search  │
│  ├── optimize_budget()         ──▶ Gemini reasoning          │
│  ├── apply_promotion()         ──▶ AlloyDB                   │
│  ├── place_order()             ──▶ AlloyDB                   │
│  └── log_session()             ──▶ BigQuery Bridge ──────┐   │
└─────────────────────────────────────────────────────────┼──┘
                                                          │
                    ┌─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  BIGQUERY BRIDGE                             │
│                                                              │
│  Tables:                                                     │
│  ├── incidents       ← ARIA writes, PULSE reads             │
│  ├── inventory_log   ← audit trail                          │
│  └── promotion_log   ← promotion effectiveness              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  PULSE — OPS AGENT                           │
│           Google ADK + Gemini 1.5 Pro                       │
│            (Vertex AI Agent Engine)                          │
│                                                              │
│  Tools (Cloud Run Functions):                                │
│  ├── detect_patterns()         ──▶ BigQuery                  │
│  ├── find_root_cause()         ──▶ BigQuery + AlloyDB        │
│  ├── predict_stockout()        ──▶ BigQuery ML               │
│  ├── draft_purchase_order()    ──▶ AlloyDB                   │
│  └── calculate_impact()        ──▶ BigQuery                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  MANAGER DASHBOARD                           │
│            Streamlit + Looker Studio                         │
│              (Cloud Run — Dashboard Service)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Technology Stack

### 5.1 AI & Agent Framework

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent Framework | **Google ADK (google-adk)** | Code-first agent definition, tool binding, ReAct loop |
| LLM — Complex reasoning | **Gemini 1.5 Pro** (Vertex AI) | ARIA cart reasoning, PULSE root cause analysis |
| LLM — Classification | **Gemini 1.5 Flash** (Vertex AI) | Intent classification, lightweight parsing |
| Agent Deployment | **Vertex AI Agent Engine** | Managed agent hosting, scaling |
| Vector Search | **AlloyDB AI (ScaNN)** | Product similarity search for substitutions |

### 5.2 Data Layer

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Operational Database | **AlloyDB for PostgreSQL** | Customer profiles, inventory, orders, promotions |
| Analytics + Bridge | **BigQuery** | Incident logging, pattern detection, BigQuery ML |
| Vector Embeddings | **AlloyDB AI + pgvector** | Product semantic search |
| Object Storage | **Cloud Storage** | Product assets, model artifacts |

### 5.3 Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Tool Functions | **Cloud Run Functions (Python)** | ARIA + PULSE tool execution |
| Agent API | **Cloud Run** | Agent endpoint serving |
| Auth | **Google Cloud IAM** | Service-to-service authentication |
| Secrets | **Secret Manager** | API keys, DB credentials |

### 5.4 Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Customer Chat UI | **Streamlit** | ARIA conversational interface |
| Manager Dashboard | **Streamlit** | PULSE pattern alerts + PO approval |
| Analytics Panel | **Looker Studio** | Embedded charts (promotion effectiveness, stockout trends) |
| Hosting | **Cloud Run** | Both Streamlit apps containerised |

### 5.5 Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Container Registry | **Artifact Registry** | Docker image storage |
| CI/CD | **Cloud Build** | Automated build + deploy |
| Monitoring | **Cloud Monitoring + Logging** | Agent reasoning traces, error tracking |
| Networking | **Cloud Load Balancing** | Traffic routing to Cloud Run services |

---

## 6. Functional Requirements

### 6.1 ARIA — CX Agent

#### FR-ARIA-01: Intent Parsing
- ARIA MUST understand natural language customer messages
- ARIA MUST extract: goal, dietary preference, budget, household size, urgency
- ARIA MUST handle ambiguous inputs by asking one clarifying question
- ARIA MUST NOT ask more than one clarifying question per session

#### FR-ARIA-02: Customer Context
- ARIA MUST retrieve customer profile before building any cart
- Customer profile MUST include: dietary preference, budget range, household size, last 3 orders
- ARIA MUST reference last order in cart building where relevant

#### FR-ARIA-03: Cart Building
- ARIA MUST build a complete cart from a customer's stated goal
- Cart MUST respect dietary restrictions (halal, vegetarian, vegan)
- Cart MUST respect stated budget
- ARIA MUST list each item with name, quantity, price, and store availability

#### FR-ARIA-04: Stock Checking
- ARIA MUST verify stock for every item before confirming in cart
- Stock check MUST include: available quantity, store location, aisle reference
- ARIA MUST flag out-of-stock items before presenting cart to customer

#### FR-ARIA-05: Substitution
- When an item is out of stock, ARIA MUST suggest at least one substitution
- Substitution MUST respect dietary restrictions
- Substitution MUST be within 20% of original item price
- ARIA MUST explain why the substitution was chosen
- Substitution search MUST use AlloyDB AI vector search for semantic similarity

#### FR-ARIA-06: Budget Optimization
- If cart total exceeds budget, ARIA MUST call optimize_budget before presenting
- ARIA MUST explain what was changed and why
- ARIA MUST achieve target budget within ±5%

#### FR-ARIA-07: Promotion Application
- ARIA MUST check available promotions when cart is within 15% of budget limit
- ARIA MUST apply the most relevant promotion automatically
- ARIA MUST inform the customer which promotion was applied and the saving
- Promotion application MUST be logged with customer_id and cart_value

#### FR-ARIA-08: Order Placement
- ARIA MUST NOT place an order without explicit customer confirmation
- Confirmation phrase MUST be one of: "confirm", "yes", "place order", "go ahead"
- Order MUST be written to AlloyDB orders table with full cart details
- Order confirmation MUST include: order_id, total, estimated delivery window

#### FR-ARIA-09: Session Logging
- ARIA MUST log every session to BigQuery incidents table regardless of outcome
- Log MUST include: customer_id, store_id, timestamp, items_ordered, items_unavailable, substitutions_offered, substitutions_accepted, promotion_applied, session_sentiment, order_placed (boolean)
- Logging MUST occur as the final step of every session

---

### 6.2 PULSE — OPS Agent

#### FR-PULSE-01: Pattern Detection
- PULSE MUST analyse the incidents table on demand and on schedule (every 6 hours)
- PULSE MUST identify products with 5+ stockout incidents in any 48-hour window
- PULSE MUST surface patterns ranked by revenue impact (highest first)

#### FR-PULSE-02: Root Cause Analysis
- For every identified stockout pattern, PULSE MUST attempt root cause analysis
- Root cause analysis MUST cross-reference: replenishment schedule, demand peak times, supplier lead times
- PULSE MUST express confidence level in root cause (high/medium/low)

#### FR-PULSE-03: Stockout Prediction
- PULSE MUST use BigQuery ML to predict next likely stockout
- Prediction MUST include: product, store, estimated time to stockout, confidence score
- PULSE MUST surface predictions with >70% confidence to the manager dashboard

#### FR-PULSE-04: Purchase Order Drafting
- For every confirmed stockout pattern, PULSE MUST draft a purchase order
- PO draft MUST include: product_id, quantity_recommended, supplier, urgency_flag, justification
- PO MUST be in a pending state until manager approves

#### FR-PULSE-05: Business Impact Calculation
- PULSE MUST calculate revenue impact for every surfaced pattern
- Calculation MUST include: revenue lost (historical), revenue at risk (forecast), revenue recoverable (if PO approved)
- All figures MUST be in AED

#### FR-PULSE-06: Manager Approval Flow
- Manager MUST be able to approve a PO with one click
- Approved POs MUST update status in AlloyDB to "approved"
- Manager MUST be able to reject with a reason (free text)
- PULSE MUST log all approval decisions with timestamp

---

### 6.3 BigQuery Bridge

#### FR-BRIDGE-01: Write Integrity
- ARIA MUST write to incidents table within 5 seconds of session completion
- Every write MUST be idempotent (session_id as primary key)
- Failed writes MUST be retried up to 3 times with exponential backoff

#### FR-BRIDGE-02: Read Freshness
- PULSE MUST read from incidents table with data no older than 15 minutes
- PULSE dashboard MUST show last_updated timestamp

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Metric | Requirement |
|--------|-------------|
| ARIA first response time | < 3 seconds |
| Cart build time (full cart) | < 8 seconds |
| Stock check per item | < 1 second |
| PULSE pattern detection | < 10 seconds |
| Dashboard load time | < 3 seconds |
| Session log write | < 5 seconds |

### 7.2 Reliability

| Metric | Requirement |
|--------|-------------|
| Agent uptime | > 99% during demo window |
| Tool function success rate | > 95% |
| BigQuery write success rate | > 99% |
| Retry on tool failure | Up to 3 retries with backoff |

### 7.3 Security

| Requirement | Implementation |
|-------------|---------------|
| Service authentication | Google Cloud IAM service accounts |
| Database credentials | Secret Manager |
| No hardcoded secrets | Enforced via .gitignore + Secret Manager |
| AlloyDB access | Private IP, VPC-only |
| Cloud Run | Authenticated invocation (IAM) |

### 7.4 Scalability
- Cloud Run MUST auto-scale from 0 to 10 instances per service
- BigQuery MUST handle up to 1,000 concurrent writes (prototype: 10)
- AlloyDB MUST support up to 100 concurrent connections (prototype: 10)

### 7.5 Observability
- Every agent tool call MUST be logged to Cloud Logging
- ReAct reasoning chain MUST be captured and displayable in UI
- Cloud Monitoring dashboard MUST show: request count, latency, error rate per tool

### 7.6 Cost (Prototype)
- Total Google Cloud spend MUST stay under $30 for the prototype build weekend
- Use BigQuery sandbox (free tier) where possible
- Cloud Run: scale to zero when idle

---

## 8. Data Model

### 8.1 AlloyDB Schema (Operational Data)

```sql
-- Customer profiles
CREATE TABLE customer_profiles (
    customer_id       VARCHAR(36) PRIMARY KEY,
    name              VARCHAR(100) NOT NULL,
    email             VARCHAR(100),
    dietary_preference VARCHAR(20) CHECK (dietary_preference IN ('halal','vegetarian','vegan','none')),
    household_size    INTEGER DEFAULT 1,
    weekly_budget_aed DECIMAL(10,2),
    preferred_store   VARCHAR(50),
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

-- Product inventory
CREATE TABLE inventory (
    product_id        VARCHAR(36) PRIMARY KEY,
    product_name      VARCHAR(200) NOT NULL,
    category          VARCHAR(100),
    brand             VARCHAR(100),
    price_aed         DECIMAL(10,2) NOT NULL,
    dietary_flags     VARCHAR(100), -- comma-separated: halal,vegetarian,vegan
    store_id          VARCHAR(50) NOT NULL,
    aisle_ref         VARCHAR(20),
    stock_quantity    INTEGER DEFAULT 0,
    reorder_threshold INTEGER DEFAULT 10,
    supplier_id       VARCHAR(36),
    embedding         vector(768), -- AlloyDB AI: product semantic embedding
    updated_at        TIMESTAMP DEFAULT NOW()
);

-- Orders
CREATE TABLE orders (
    order_id          VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id       VARCHAR(36) REFERENCES customer_profiles(customer_id),
    store_id          VARCHAR(50) NOT NULL,
    items             JSONB NOT NULL, -- [{product_id, quantity, price_aed}]
    total_aed         DECIMAL(10,2) NOT NULL,
    promotion_id      VARCHAR(36),
    promotion_saving  DECIMAL(10,2) DEFAULT 0,
    status            VARCHAR(20) DEFAULT 'confirmed' CHECK (status IN ('confirmed','processing','delivered','cancelled')),
    delivery_window   TSTZRANGE,
    created_at        TIMESTAMP DEFAULT NOW()
);

-- Promotions
CREATE TABLE promotions (
    promotion_id      VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(200) NOT NULL,
    category          VARCHAR(100),
    discount_pct      DECIMAL(5,2),
    min_cart_aed      DECIMAL(10,2) DEFAULT 0,
    max_uses          INTEGER,
    times_applied     INTEGER DEFAULT 0,
    valid_from        TIMESTAMP NOT NULL,
    valid_until       TIMESTAMP NOT NULL,
    is_active         BOOLEAN DEFAULT true
);

-- Replenishment schedules
CREATE TABLE replenishment_schedule (
    schedule_id       VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id          VARCHAR(50) NOT NULL,
    product_id        VARCHAR(36) REFERENCES inventory(product_id),
    supplier_id       VARCHAR(36),
    delivery_day      VARCHAR(20), -- Monday, Tuesday, etc.
    delivery_time     TIME,
    quantity_per_delivery INTEGER,
    lead_time_days    INTEGER DEFAULT 1
);

-- Purchase orders (PULSE creates, manager approves)
CREATE TABLE purchase_orders (
    po_id             VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id        VARCHAR(36) REFERENCES inventory(product_id),
    store_id          VARCHAR(50) NOT NULL,
    quantity          INTEGER NOT NULL,
    urgency           VARCHAR(10) CHECK (urgency IN ('low','medium','high','critical')),
    justification     TEXT,
    revenue_at_risk   DECIMAL(10,2),
    status            VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
    manager_note      TEXT,
    created_by        VARCHAR(20) DEFAULT 'PULSE',
    created_at        TIMESTAMP DEFAULT NOW(),
    reviewed_at       TIMESTAMP
);
```

### 8.2 BigQuery Schema (Analytics Bridge)

```sql
-- Main bridge table: ARIA writes, PULSE reads
CREATE TABLE arc_dataset.incidents (
    session_id            STRING NOT NULL,
    customer_id           STRING,
    store_id              STRING,
    timestamp             TIMESTAMP,
    items_ordered         JSON,      -- [{product_id, name, qty, price}]
    items_unavailable     JSON,      -- [{product_id, name}]
    substitutions_offered JSON,      -- [{original_id, substitute_id, accepted: bool}]
    promotion_applied     STRING,    -- promotion_id or null
    promotion_saving_aed  FLOAT64,
    cart_total_aed        FLOAT64,
    session_sentiment     STRING,    -- positive / neutral / negative
    order_placed          BOOL,
    abandonment_reason    STRING     -- null if order placed
);

-- Inventory change audit log
CREATE TABLE arc_dataset.inventory_log (
    log_id        STRING NOT NULL,
    product_id    STRING,
    store_id      STRING,
    event_type    STRING, -- stockout / restock / adjustment
    quantity_before INTEGER,
    quantity_after  INTEGER,
    logged_at     TIMESTAMP
);

-- Promotion effectiveness log
CREATE TABLE arc_dataset.promotion_log (
    log_id          STRING NOT NULL,
    promotion_id    STRING,
    customer_id     STRING,
    cart_before_aed FLOAT64,
    cart_after_aed  FLOAT64,
    saving_aed      FLOAT64,
    converted       BOOL,
    logged_at       TIMESTAMP
);
```

---

## 9. Agent Specifications

### 9.1 ARIA System Prompt

```
You are ARIA, an AI shopping assistant for MIRA Retail UAE.

Your purpose is to help customers build their grocery cart based on 
their goals, dietary preferences, and budget — and to resolve any 
shopping friction they encounter.

## Strict Sequencing Rules
1. ALWAYS call get_customer_context() as the first tool, before anything else
2. ALWAYS call check_stock() for every item before adding to cart
3. ALWAYS call suggest_substitution() before telling a customer an item is unavailable
4. ALWAYS call optimize_budget() if cart total exceeds customer budget
5. ALWAYS call apply_promotion() after budget optimization
6. NEVER call place_order() without explicit customer confirmation
7. ALWAYS call log_session() as the absolute final step — even if no order was placed

## Confirmation Rules
Only place an order when the customer says one of: 
"confirm", "yes", "place order", "go ahead", "proceed"

## Dietary Rules
- NEVER suggest non-halal products to customers with halal preference
- NEVER suggest meat products to vegetarian or vegan customers
- Always verify dietary_flags before recommending any product

## Communication Style
- Be helpful, concise, and warm
- Explain your reasoning in plain language
- When optimizing budget, tell the customer specifically what changed and why
- When applying a promotion, tell the customer the saving amount
- If you cannot help with something, politely redirect to grocery shopping

## Error Handling
- If a tool call fails, tell the customer there was a brief issue and retry once
- If retry fails, offer to continue with the items that succeeded
```

### 9.2 PULSE System Prompt

```
You are PULSE, an operations intelligence agent for MIRA Retail store managers.

Your purpose is to analyse customer interaction patterns from the 
incidents table and surface actionable operational insights — 
stockout patterns, root causes, and purchase order recommendations.

## Strict Sequencing Rules
1. ALWAYS call detect_patterns() first, covering the last 48 hours
2. ALWAYS call find_root_cause() for every pattern with 5+ incidents
3. ALWAYS call calculate_impact() before drafting any purchase order
4. ALWAYS call draft_purchase_order() for confirmed stockout patterns
5. NEVER recommend action without supporting data from the incidents table
6. NEVER draft a PO without calculating business impact first

## Communication Style
- Be analytical, precise, and concise
- Always lead with the business impact (AED) before explaining the cause
- Express confidence level for every root cause (High / Medium / Low)
- Use plain language — the manager is not a data scientist

## Report Structure
For every surfaced pattern, always follow this structure:
1. What: product + store + incident count
2. Impact: revenue lost (AED) + revenue at risk (AED)
3. Why: root cause + confidence level
4. Action: draft PO details
5. Recovery: estimated revenue recoverable if PO approved
```

### 9.3 Agent Tool Definitions (Google ADK)

```python
# ARIA Tools — defined using Google ADK
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

def parse_intent(customer_message: str) -> dict:
    """
    Extracts structured intent from a customer's natural language message.
    Returns goal, dietary_preference, budget_aed, household_size, urgency.
    Call this first when a customer sends their initial shopping request.
    Do NOT call this for follow-up messages in an ongoing session.
    """
    pass

def get_customer_context(customer_id: str) -> dict:
    """
    Retrieves the customer's profile and last 3 orders from AlloyDB.
    Returns: dietary_preference, weekly_budget_aed, household_size,
    preferred_store, last_orders [list of product_ids].
    Always call this before building any cart. Never skip this step.
    """
    pass

def build_cart(
    goal: str,
    dietary_preference: str,
    budget_aed: float,
    household_size: int,
    store_id: str
) -> dict:
    """
    Builds a grocery cart from AlloyDB inventory matching the customer goal.
    Filters by dietary_preference and sorts by value within budget_aed.
    Returns: items [list], total_aed, items_unavailable [list].
    Call after get_customer_context(). Always pass dietary_preference.
    """
    pass

def check_stock(product_id: str, store_id: str) -> dict:
    """
    Checks real-time stock for a specific product at a specific store.
    Returns: available (bool), quantity, aisle_ref, alternative_stores [list].
    Call for every item before confirming it in the cart.
    """
    pass

def suggest_substitution(
    product_id: str,
    store_id: str,
    dietary_preference: str,
    max_price_aed: float
) -> dict:
    """
    Uses AlloyDB AI vector search (ScaNN) to find semantically similar
    in-stock products matching dietary_preference and within max_price_aed.
    Returns: substitute_product_id, name, price_aed, similarity_score, reason.
    Call immediately when check_stock() returns available=False.
    Never tell a customer an item is unavailable before calling this.
    """
    pass

def optimize_budget(cart: list, target_budget_aed: float) -> dict:
    """
    Trims or swaps cart items to bring total within target_budget_aed.
    Uses Gemini reasoning to select the least impactful items to adjust.
    Returns: updated_cart [list], new_total_aed, changes_made [list].
    Call when cart total exceeds customer budget. Always explain changes.
    """
    pass

def apply_promotion(
    cart: list,
    cart_total_aed: float,
    dietary_preference: str
) -> dict:
    """
    Checks AlloyDB promotions table for applicable active promotions.
    Applies the highest-value relevant promotion matching dietary_preference.
    Returns: promotion_id, promotion_name, discount_aed, new_total_aed.
    Call after optimize_budget(). If no promotion applies, return null.
    """
    pass

def place_order(
    customer_id: str,
    store_id: str,
    cart: list,
    promotion_id: str,
    total_aed: float
) -> dict:
    """
    Writes the confirmed order to AlloyDB orders table.
    Returns: order_id, status, estimated_delivery_window.
    Only call after receiving explicit customer confirmation.
    Confirmation phrases: confirm / yes / place order / go ahead / proceed.
    """
    pass

def log_session(
    session_id: str,
    customer_id: str,
    store_id: str,
    items_ordered: list,
    items_unavailable: list,
    substitutions: list,
    promotion_id: str,
    promotion_saving: float,
    cart_total: float,
    sentiment: str,
    order_placed: bool
) -> dict:
    """
    Writes the complete session summary to BigQuery incidents table.
    This is the bridge between ARIA and PULSE.
    ALWAYS call this as the absolute last step of every session.
    Never skip this — even if no order was placed.
    sentiment must be one of: positive / neutral / negative
    """
    pass
```

---

## 10. API Contracts

### 10.1 Tool Function Response Schemas

```python
# parse_intent response
{
    "goal": str,                    # "weekly groceries", "biryani ingredients"
    "dietary_preference": str,      # halal | vegetarian | vegan | none
    "budget_aed": float,
    "household_size": int,
    "urgency": str                  # normal | urgent
}

# get_customer_context response
{
    "customer_id": str,
    "name": str,
    "dietary_preference": str,
    "household_size": int,
    "weekly_budget_aed": float,
    "preferred_store": str,
    "last_orders": [
        {"product_id": str, "product_name": str, "last_ordered": str}
    ]
}

# build_cart response
{
    "items": [
        {
            "product_id": str,
            "product_name": str,
            "quantity": int,
            "price_aed": float,
            "aisle_ref": str,
            "in_stock": bool
        }
    ],
    "total_aed": float,
    "items_unavailable": [
        {"product_id": str, "product_name": str}
    ]
}

# check_stock response
{
    "product_id": str,
    "available": bool,
    "quantity": int,
    "aisle_ref": str,
    "alternative_stores": [
        {"store_id": str, "store_name": str, "quantity": int}
    ]
}

# suggest_substitution response
{
    "substitute_product_id": str,
    "name": str,
    "price_aed": float,
    "similarity_score": float,
    "reason": str,
    "in_stock": bool
}

# place_order response
{
    "order_id": str,
    "status": str,
    "total_aed": float,
    "estimated_delivery_window": str
}

# log_session response
{
    "session_id": str,
    "logged": bool,
    "timestamp": str
}

# detect_patterns response (PULSE)
{
    "patterns": [
        {
            "product_id": str,
            "product_name": str,
            "store_id": str,
            "incident_count": int,
            "period_hours": int,
            "revenue_lost_aed": float,
            "peak_time": str
        }
    ]
}

# draft_purchase_order response (PULSE)
{
    "po_id": str,
    "product_id": str,
    "quantity": int,
    "urgency": str,
    "justification": str,
    "revenue_at_risk_aed": float,
    "revenue_recoverable_aed": float,
    "status": "pending"
}
```

---

## 11. Frontend Specification

### 11.1 ARIA Chat Interface (Streamlit)

**File:** `frontend/aria_chat.py`

**Components:**
- Chat input (text, bottom of screen)
- Message history (scrollable, styled bubbles)
- Cart preview panel (right sidebar, updates in real time)
- Reasoning chain expander (collapsible "How did ARIA decide this?" panel)
- Order confirmation button (appears only when cart is complete)
- Session ID display (for debugging)

**Reasoning chain display format:**
```
▼ How did ARIA decide this?
  🤔 THOUGHT: Customer wants weekly groceries, halal, AED 300
  🔧 ACTION: get_customer_context(customer_id=sarah_123)
  👁 OBSERVATION: {halal, budget:300, household:4}
  🤔 THOUGHT: Build cart within constraints
  🔧 ACTION: build_cart(goal=weekly, dietary=halal, budget=300)
  ...
```

**Cart preview format:**
```
🛒 Your Cart
────────────────────
Basmati Rice 2kg     AED 18.00
Almarai Milk 2L      AED 12.00
Halal Chicken 1kg    AED 34.00
...
────────────────────
Subtotal:            AED 287.00
Promotion applied:   -AED 13.00
Total:               AED 274.00
```

### 11.2 PULSE Manager Dashboard (Streamlit)

**File:** `frontend/pulse_dashboard.py`

**Components:**
- Alert cards (top, ranked by revenue impact)
- Root cause panel (expandable per alert)
- Purchase order panel (with one-click approve/reject)
- Promotion effectiveness chart (Looker Studio embedded)
- Stockout trend chart (Looker Studio embedded)
- Last updated timestamp
- Refresh button

**Alert card format:**
```
⚠️ BROWN RICE STOCKOUT — Dubai Marina
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
23 incidents in 48 hours
Revenue lost: AED 847
Revenue at risk: AED 2,400/week

Root cause (High confidence):
Delivery arrives Tuesday 2PM
Demand peaks Monday-Wednesday 10AM-12PM
→ 4-hour supply gap

[📋 Draft PO Ready]  [✅ Approve]  [❌ Reject]
```

---

## 12. Infrastructure & Deployment

### 12.1 Google Cloud Project Structure

```
Project: arc-retail-hackathon
├── Region: asia-southeast1 (Singapore — closest to UAE for demo)
│
├── Compute
│   ├── Cloud Run: aria-agent-service
│   ├── Cloud Run: pulse-agent-service
│   ├── Cloud Run: aria-chat-frontend
│   ├── Cloud Run: pulse-dashboard-frontend
│   └── Cloud Run: tool-functions-service
│
├── Data
│   ├── AlloyDB: arc-alloydb-cluster
│   │   └── Primary instance: arc-alloydb-primary
│   ├── BigQuery: arc_dataset
│   │   ├── incidents
│   │   ├── inventory_log
│   │   └── promotion_log
│   └── Cloud Storage: arc-assets-bucket
│
├── AI
│   ├── Vertex AI Agent Engine: aria-agent
│   ├── Vertex AI Agent Engine: pulse-agent
│   └── Vertex AI Model: gemini-1.5-pro
│
└── DevOps
    ├── Artifact Registry: arc-registry
    ├── Cloud Build: arc-build-trigger
    └── Secret Manager: arc-secrets
```

### 12.2 Environment Variables

```env
# Google Cloud
GOOGLE_CLOUD_PROJECT=arc-retail-hackathon
GOOGLE_CLOUD_REGION=asia-southeast1

# AlloyDB
ALLOYDB_HOST=<private-ip>
ALLOYDB_PORT=5432
ALLOYDB_DATABASE=arc_db
ALLOYDB_USER=arc_user
ALLOYDB_PASSWORD=<secret-manager>

# BigQuery
BIGQUERY_DATASET=arc_dataset

# Vertex AI
VERTEX_AI_LOCATION=asia-southeast1
GEMINI_MODEL=gemini-1.5-pro
GEMINI_FLASH_MODEL=gemini-1.5-flash

# Agent Engine
ARIA_AGENT_ID=<agent-id>
PULSE_AGENT_ID=<agent-id>
```

### 12.3 Docker Configuration

```dockerfile
# Base Dockerfile for all Cloud Run services
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "main.py"]
```

---

## 13. Project Setup

### 13.1 Repository Structure

```
arc/
├── README.md
├── SPEC.md                          ← this file
├── .gitignore
├── .env.example
│
├── agents/
│   ├── aria/
│   │   ├── agent.py                 ← Google ADK agent definition
│   │   ├── system_prompt.txt        ← ARIA system prompt
│   │   ├── tools.py                 ← Tool function definitions
│   │   └── requirements.txt
│   └── pulse/
│       ├── agent.py                 ← Google ADK agent definition
│       ├── system_prompt.txt        ← PULSE system prompt
│       ├── tools.py                 ← Tool function definitions
│       └── requirements.txt
│
├── tools/
│   ├── aria_tools/
│   │   ├── parse_intent.py
│   │   ├── get_customer_context.py
│   │   ├── build_cart.py
│   │   ├── check_stock.py
│   │   ├── suggest_substitution.py
│   │   ├── optimize_budget.py
│   │   ├── apply_promotion.py
│   │   ├── place_order.py
│   │   └── log_session.py
│   └── pulse_tools/
│       ├── detect_patterns.py
│       ├── find_root_cause.py
│       ├── predict_stockout.py
│       ├── draft_purchase_order.py
│       └── calculate_impact.py
│
├── data/
│   ├── schema/
│   │   ├── alloydb_schema.sql       ← AlloyDB table definitions
│   │   └── bigquery_schema.sql      ← BigQuery table definitions
│   └── seed/
│       ├── customer_profiles.sql    ← Mock customer data
│       ├── inventory.sql            ← Mock MIRA Retail grocery inventory
│       ├── promotions.sql           ← Mock promotions
│       └── replenishment.sql        ← Mock replenishment schedules
│
├── frontend/
│   ├── aria_chat.py                 ← Streamlit customer chat
│   ├── pulse_dashboard.py           ← Streamlit manager dashboard
│   └── requirements.txt
│
├── infrastructure/
│   ├── cloudbuild.yaml              ← CI/CD pipeline
│   ├── alloydb_setup.sh             ← AlloyDB provisioning script
│   └── bigquery_setup.sh            ← BigQuery dataset setup
│
└── tests/
    ├── test_aria_tools.py
    ├── test_pulse_tools.py
    └── test_bridge.py
```

### 13.2 Initial Setup Commands

```bash
# 1. Clone repo
git clone https://github.com/pragmatic-engineers/arc
cd arc

# 2. Set up Python environment
python -m venv venv
source venv/bin/activate
pip install google-adk google-cloud-bigquery google-cloud-aiplatform \
            google-cloud-alloydb-connector pg8000 streamlit \
            google-cloud-secret-manager

# 3. Authenticate Google Cloud
gcloud auth application-default login
gcloud config set project arc-retail-hackathon

# 4. Enable required APIs
gcloud services enable \
    aiplatform.googleapis.com \
    alloydb.googleapis.com \
    bigquery.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com

# 5. Set up AlloyDB
bash infrastructure/alloydb_setup.sh

# 6. Run AlloyDB schema
psql -h $ALLOYDB_HOST -U arc_user -d arc_db -f data/schema/alloydb_schema.sql

# 7. Seed mock data
psql -h $ALLOYDB_HOST -U arc_user -d arc_db -f data/seed/customer_profiles.sql
psql -h $ALLOYDB_HOST -U arc_user -d arc_db -f data/seed/inventory.sql
psql -h $ALLOYDB_HOST -U arc_user -d arc_db -f data/seed/promotions.sql
psql -h $ALLOYDB_HOST -U arc_user -d arc_db -f data/seed/replenishment.sql

# 8. Set up BigQuery
bash infrastructure/bigquery_setup.sh

# 9. Run ARIA locally (ADK dev server)
cd agents/aria
adk web .

# 10. Run PULSE locally
cd agents/pulse
adk web .

# 11. Run Streamlit frontends
streamlit run frontend/aria_chat.py
streamlit run frontend/pulse_dashboard.py
```

### 13.3 Google ADK Agent Definition (ARIA)

```python
# agents/aria/agent.py
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from tools.aria_tools.parse_intent import parse_intent
from tools.aria_tools.get_customer_context import get_customer_context
from tools.aria_tools.build_cart import build_cart
from tools.aria_tools.check_stock import check_stock
from tools.aria_tools.suggest_substitution import suggest_substitution
from tools.aria_tools.optimize_budget import optimize_budget
from tools.aria_tools.apply_promotion import apply_promotion
from tools.aria_tools.place_order import place_order
from tools.aria_tools.log_session import log_session

with open("system_prompt.txt") as f:
    system_prompt = f.read()

aria_agent = Agent(
    name="ARIA",
    model="gemini-1.5-pro",
    description="MIRA Retail UAE customer shopping assistant",
    instruction=system_prompt,
    tools=[
        FunctionTool(parse_intent),
        FunctionTool(get_customer_context),
        FunctionTool(build_cart),
        FunctionTool(check_stock),
        FunctionTool(suggest_substitution),
        FunctionTool(optimize_budget),
        FunctionTool(apply_promotion),
        FunctionTool(place_order),
        FunctionTool(log_session),
    ]
)
```

---

## 14. Build Plan

| Day | Owner | Tasks | Output |
|-----|-------|-------|--------|
| **Fri Oct 16** | Both | Schema design, mock data, GCP setup | AlloyDB + BigQuery ready with seed data |
| **Sat Oct 17 AM** | Partner | ARIA tool functions (9 Cloud Run functions) | All ARIA tools tested individually |
| **Sat Oct 17 PM** | You | ARIA agent wiring (ADK) + Streamlit chat UI | ARIA end-to-end working |
| **Sat Oct 17 PM** | Partner | PULSE tool functions (5 Cloud Run functions) | All PULSE tools tested individually |
| **Sun Oct 18 AM** | Both | PULSE agent wiring + Manager dashboard + BigQuery bridge test | Full end-to-end flow working |
| **Sun Oct 18 PM** | You | Demo video (5 min) + Pitch deck (10 slides) + GitHub README | Submission package ready |
| **Sun Oct 18 EOD** | You | Submit via AI Builder Cup portal | ✅ Submitted |

---

## 15. Demo Script

### Scene 1: Customer Chat (ARIA) — 90 seconds
- Sarah types: *"Weekly groceries, family of 4, halal diet, AED 300 budget"*
- Show reasoning chain expanding in real time
- Cart builds item by item
- Brown rice flagged as out of stock → substitution suggested
- Budget optimization: AED 334 → AED 291
- Promotion applied: AED 13 saved
- Sarah confirms: "Yes, place the order"
- Order confirmed, session logged to BigQuery

### Scene 2: The Bridge — 20 seconds
- Switch to BigQuery incidents table
- Show one new row just written
- *"ARIA just wrote this. PULSE is already reading it."*

### Scene 3: Manager Dashboard (PULSE) — 90 seconds
- Ahmed's dashboard shows brown rice alert
- 23 incidents, AED 847 lost, root cause identified
- Draft PO appears — pre-filled
- Ahmed clicks Approve
- PO status updates to approved

### Scene 4: The Loop Closes — 30 seconds
- Show the ARC flow diagram
- *"One customer interaction. Two agents. Zero manual steps."*
- *"Tomorrow, Sarah finds brown rice in stock."*

**Total: ~4 minutes 10 seconds**

---

## 16. Success Criteria

### Hackathon Judging Criteria

| Criteria | Weight | Our Target |
|----------|--------|------------|
| Technical Merit | 40% | Full Google Cloud stack, ADK, AlloyDB AI, BigQuery ML |
| Problem Alignment | 25% | Hits conversational commerce + inventory intelligence + customer insights |
| Innovation | 25% | Closed loop: no comparable submission expected |
| UX | 10% | Clean chat UI + visible reasoning + one-click PO approval |

### Demo Success Criteria
- [ ] ARIA completes a full cart-to-order journey without errors
- [ ] BigQuery bridge row visible immediately after order
- [ ] PULSE surfaces the correct pattern from the bridge data
- [ ] Manager can approve a PO in one click
- [ ] Reasoning chain visible and legible in ARIA UI
- [ ] Demo completes within 5 minutes

### Technical Success Criteria
- [ ] All 14 tool functions deployed and callable
- [ ] AlloyDB seeded with realistic MIRA Retail mock data
- [ ] BigQuery incidents table receiving writes from ARIA
- [ ] PULSE reading patterns from BigQuery correctly
- [ ] Both Streamlit frontends deployed on Cloud Run
- [ ] End-to-end latency under 10 seconds for full cart build

---

*ARC — Agentic Retail Command | Pragmatic Engineers | AI Builder Cup 2026*
*Spec version 1.0 | Last updated: Oct 16, 2026*
