# AGENT_CONTRACTS.md — Tool Function API Contracts
> MIRA Retail · ARC v1.0
> Updated: Lessons from Agentic Cinema winning projects applied

All tool functions are Python functions decorated as Google ADK `FunctionTool`s.
They are deployed as Cloud Run Functions and called by the ADK agent runtime.
All inputs and outputs are JSON-serializable Python dicts.

---

## ARIA tool functions (9)

### 1. parse_intent

**Docstring (drives agent reasoning):**
```
Extracts structured intent from a customer's natural language message.
Returns goal, dietary_preference, budget_aed, household_size, urgency.
Call this first when a customer sends their initial shopping request.
Do NOT call this for follow-up messages in an ongoing session.
```

**Input:**
```python
customer_message: str
```

**Output:**
```python
{
    "goal": str,
    "dietary_preference": str,      # "halal" | "vegetarian" | "vegan" | "none"
    "budget_aed": float,
    "household_size": int,
    "urgency": str                  # "normal" | "urgent"
}
```

---

### 2. get_customer_context

**Docstring:**
```
Retrieves the customer's profile and last 3 orders from AlloyDB.
Returns dietary_preference, weekly_budget_aed, household_size,
preferred_store, last_orders list.
Always call this before building any cart. Never skip this step.
```

**Input:** `customer_id: str`

**Output:**
```python
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
```

---

### 3. build_cart

**Docstring:**
```
Builds a grocery cart from AlloyDB inventory matching the customer goal.
Restricted to grocery categories only: dairy, grains, halal meat,
vegetables, fruits, beverages, snacks, condiments.
Filters by dietary_preference. Selects best-value items within budget_aed.
Returns items list, total_aed, and items_unavailable list.
Call after get_customer_context(). Always pass dietary_preference.
```

**Input:**
```python
goal: str
dietary_preference: str
budget_aed: float
household_size: int
store_id: str
```

**Output:**
```python
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
```

---

### 4. check_stock

**Docstring:**
```
Checks real-time stock for a specific product at a specific store.
Returns available bool, quantity, aisle_ref, and alternative_stores list.
Call for every item before confirming it in the cart.
```

**Input:** `product_id: str`, `store_id: str`

**Output:**
```python
{
    "product_id": str,
    "available": bool,
    "quantity": int,
    "aisle_ref": str,
    "alternative_stores": [
        {"store_id": str, "store_name": str, "quantity": int, "distance_km": float}
    ]
}
```

---

### 5. suggest_substitution

**Docstring:**
```
Uses AlloyDB AI vector search (ScaNN) to find semantically similar
in-stock products matching dietary_preference and within max_price_aed.
Returns substitute_product_id, name, price_aed, similarity_score, reason.
Call immediately when check_stock() returns available=False.
Never tell a customer an item is unavailable before calling this.
```

**Input:**
```python
product_id: str
store_id: str
dietary_preference: str
max_price_aed: float
```

**Output:**
```python
{
    "substitute_product_id": str,
    "name": str,
    "price_aed": float,
    "similarity_score": float,
    "reason": str,
    "in_stock": bool
}
```

---

### 6. optimize_budget

**Docstring:**
```
Trims or swaps cart items to bring total within target_budget_aed.
Uses Gemini reasoning to select the least impactful items to adjust.
Returns updated_cart, new_total_aed, and changes_made list.
Call when cart total exceeds customer budget. Always explain changes.
```

**Input:**
```python
cart: list[dict]
target_budget_aed: float
dietary_preference: str
```

**Output:**
```python
{
    "updated_cart": list[dict],
    "new_total_aed": float,
    "changes_made": [
        {"action": str, "product_name": str, "saving_aed": float}
    ]
}
```

---

### 7. apply_promotion

**Docstring:**
```
Checks AlloyDB promotions table for applicable active promotions.
Applies the highest-value relevant promotion matching dietary_preference.
Returns promotion_id, promotion_name, discount_aed, new_total_aed.
Call after optimize_budget(). If no promotion applies, return null.
```

**Input:**
```python
cart: list[dict]
cart_total_aed: float
dietary_preference: str
store_id: str
```

**Output:**
```python
{
    "promotion_applied": bool,
    "promotion_id": str | None,
    "promotion_name": str | None,
    "discount_aed": float,
    "new_total_aed": float,
    "reason": str
}
```

---

### 8. place_order

**Docstring:**
```
Writes the confirmed order to AlloyDB orders table.
Returns order_id, status, estimated_delivery_window.
Only call after receiving explicit customer confirmation.
Confirmation phrases: confirm / yes / place order / go ahead / proceed.
```

**Input:**
```python
customer_id: str
store_id: str
cart: list[dict]
promotion_id: str | None
total_aed: float
```

**Output:**
```python
{
    "order_id": str,
    "status": str,
    "total_aed": float,
    "estimated_delivery_window": str
}
```

---

### 9. log_session

**Docstring:**
```
Writes the complete session summary to BigQuery incidents table.
This is the bridge between ARIA and PULSE.
ALWAYS call this as the absolute last step of every session.
Never skip this — even if no order was placed.
sentiment must be one of: positive / neutral / negative
This write is what enables PULSE to detect patterns and surface
operational intelligence to store managers.
```

**Input:**
```python
session_id: str
customer_id: str
store_id: str
items_ordered: list[dict]
items_unavailable: list[dict]
substitutions: list[dict]
promotion_id: str | None
promotion_saving_aed: float
cart_total_aed: float
budget_aed: float
sentiment: str
order_placed: bool
abandonment_reason: str | None
```

**Output:**
```python
{
    "session_id": str,
    "logged": bool,
    "timestamp": str
}
```

---

## PULSE tool functions (5)

### 1. detect_patterns

**Docstring:**
```
Queries BigQuery incidents table for products with 5+ stockout incidents
in any 48-hour window, ranked by estimated revenue impact in AED.
Returns patterns list with incident counts, revenue estimates, and
the exact evidence rows that support each pattern.
Always call this first — it is the starting point for all PULSE analysis.
Revenue impact is calculated as: incident_count × average_cart_aed × 0.15
(estimated margin at risk per stockout event).
```

**Input:**
```python
store_id: str
hours: int = 48
min_incidents: int = 5
```

**Output:**
```python
{
    "patterns": [
        {
            "product_id": str,
            "product_name": str,
            "store_id": str,
            "incident_count": int,
            "period_hours": int,
            "estimated_revenue_lost_aed": float,
            "peak_hour": str,
            "abandonment_count": int,
            "evidence": {
                "first_incident": str,      # ISO timestamp
                "last_incident": str,       # ISO timestamp
                "sample_session_ids": list[str],  # up to 3 session IDs
                "substitution_acceptance_rate": float
            }
        }
    ]
}
```

---

### 2. find_root_cause

**Docstring:**
```
Cross-references a stockout pattern with the replenishment schedule
in AlloyDB to identify the root cause of the supply gap.
Returns root_cause, confidence_level, plain-language explanation,
AND a structured evidence block citing the exact data used.
The evidence block is mandatory — never return a root cause without it.
Call after detect_patterns() for every pattern with revenue impact > AED 500.
```

**Input:**
```python
product_id: str
store_id: str
peak_hour: str
incident_count: int
period_hours: int
```

**Output:**
```python
{
    "root_cause": str,
    "confidence_level": str,        # "High" | "Medium" | "Low"
    "explanation": str,             # plain English for manager
    "evidence": {
        "delivery_day": str,
        "delivery_time": str,
        "demand_peak_window": str,
        "gap_hours": int,
        "data_sources": [
            "BigQuery incidents table: 23 rows, Oct 14-16 2026",
            "AlloyDB replenishment_schedule: store=dubai_marina_01, product=brown_rice"
        ]
    },
    "recommended_action": str       # plain English recommendation
}
```

---

### 3. predict_stockout

**Docstring:**
```
Uses BigQuery ML ARIMA_PLUS model to forecast next stockout for a product.
Only surfaces predictions with confidence >= 0.70.
Returns predicted_date, confidence, days_until_stockout, and evidence.
Call after find_root_cause() to add predictive intelligence to the alert.
```

**Input:**
```python
product_id: str
store_id: str
forecast_days: int = 7
```

**Output:**
```python
{
    "predicted_stockout_date": str,
    "days_until_stockout": int,
    "confidence": float,
    "current_stock": int,
    "daily_consumption_rate": float,
    "evidence": {
        "model": "BigQuery ML ARIMA_PLUS",
        "training_period": str,
        "data_points_used": int
    }
}
```

---

### 4. calculate_impact

**Docstring:**
```
Calculates business impact in AED for a confirmed stockout pattern.
Returns revenue_lost (historical), revenue_at_risk (forecast),
and revenue_recoverable (if PO is approved today).
Always call this before drafting a purchase order.
Never draft a PO without calculating impact first.
The impact calculation must cite its basis in plain language
so the manager can verify the numbers independently.
```

**Input:**
```python
product_id: str
store_id: str
incident_count: int
average_cart_aed: float
abandonment_count: int
days_to_next_delivery: int
```

**Output:**
```python
{
    "revenue_lost_aed": float,
    "revenue_at_risk_aed": float,
    "revenue_recoverable_aed": float,
    "calculation_basis": str,
    "evidence": {
        "incidents_used": int,
        "average_cart_aed": float,
        "abandonment_rate": float,
        "formula": "incident_count × avg_cart × abandonment_rate × margin_pct"
    }
}
```

---

### 5. draft_purchase_order

**Docstring:**
```
Creates a pending purchase order in AlloyDB purchase_orders table.
The PO is in PENDING status until the manager explicitly approves
or rejects it. The system never auto-approves.
Human approval is required for every purchase order — always.
Returns po_id and full PO details including the evidence summary
so the manager can see exactly why this PO was recommended.
Only call after calculate_impact() — never draft without impact data.
```

**Input:**
```python
product_id: str
store_id: str
quantity: int
urgency: str
justification: str
revenue_at_risk_aed: float
revenue_recoverable_aed: float
evidence_summary: str
```

**Output:**
```python
{
    "po_id": str,
    "product_id": str,
    "product_name": str,
    "quantity": int,
    "urgency": str,
    "justification": str,
    "revenue_at_risk_aed": float,
    "revenue_recoverable_aed": float,
    "evidence_summary": str,
    "status": "pending",
    "human_approval_required": True,    # always True — never auto-approve
    "created_at": str
}
```

---

## Error response format (all tools)

```python
{
    "error": True,
    "error_code": str,
    "error_message": str,
    "retry_suggested": bool
}
```

---

*MIRA Retail · ARC v1.0 · Agent Contracts v1.1 — evidence citations added*
