# SPEC-PULSE-06: execute_perishable_discount
> MIRA Retail · ARC Project · PULSE OPS Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `execute_perishable_discount`  
**Agent:** PULSE (OPS Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → AlloyDB + BigQuery  
**Purpose:** Monitor perishable inventory items whose sell-through velocity will not clear stock before expiry. When the trigger condition is met, calculate the appropriate discount tier and surface a discount proposal to the manager for approval.

**Why it exists:** Perishable waste is a direct revenue loss. Every unit of Laban that expires unsold is AED 8 thrown away. PULSE can predict this 1-3 days in advance and propose a targeted discount that turns waste into revenue — but only with the manager's explicit approval.

**The trigger condition:**  
`days_to_expiry × daily_sales_rate < current_stock_quantity`

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `store_id` | string | Yes | Must exist in stores |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate store_id

Step 2: Query AlloyDB for all perishable items at this store
        → SELECT product_id, product_name, price_aed,
                 stock_quantity, expiry_date, is_perishable
          FROM inventory
          WHERE store_id = $1
          AND is_perishable = true
          AND stock_quantity > 0
          AND expiry_date IS NOT NULL
          AND expiry_date <= CURRENT_DATE + INTERVAL '3 days'

Step 3: For each perishable item, calculate daily_sales_rate
        → Query BigQuery incidents for last 7 days
          SELECT SUM(ordered_qty) / 7 as daily_rate
          FROM arc_dataset.incidents
          WHERE store_id = $1
          AND product_id = $2
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)

Step 4: Apply trigger condition
        → days_to_expiry = expiry_date - CURRENT_DATE
        → projected_sell_through = days_to_expiry × daily_sales_rate
        → triggered = projected_sell_through < stock_quantity

Step 5: For triggered items, calculate discount tier
        → 1 day: 40%
        → 2 days: 25%
        → 3 days: 15%

Step 6: Calculate financials
        → units_at_risk = stock_quantity - projected_sell_through
        → revenue_at_risk = units_at_risk × price_aed
        → discounted_price = price_aed × (1 - discount_pct / 100)
        → expected_additional_sell = units_at_risk × 0.60 (60% discount conversion)
        → revenue_recoverable = expected_additional_sell × discounted_price

Step 7: Build evidence block
        → Include trigger_formula with actual numbers
        → Include data sources (inventory + BigQuery)

Step 8: Return ExecutePerishableDiscountResponse
        → status = "pending" for all alerts
        → human_approval_required = true for all alerts
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| store_id not empty | len(strip(id)) >= 1 | VALIDATION_ERROR |
| store_id exists | In stores table | NOT_FOUND |

### Output sanity checks
| Check | Rule |
|-------|------|
| Only is_perishable=true items | Non-perishable items never in alerts |
| Trigger condition verified | days_to_expiry × daily_sales_rate < stock_quantity |
| discount_pct valid | Must be exactly 15.0, 25.0, or 40.0 |
| days_to_expiry 1-3 only | Items > 3 days not triggered |
| discounted_price correct | price × (1 - pct/100) rounded to 2dp |
| revenue_recoverable <= revenue_at_risk | Cannot recover more than at risk |
| status always "pending" | Never "approved" on creation |
| human_approval_required always true | Never false |
| Empty alert valid | No triggered items = return empty array |
| evidence.trigger_formula | Must show actual calculated numbers |

---

## 5. OUTPUTS

**Alerts found:**
```json
{
  "perishable_alerts": [
    {
      "product_id": "laban_almarai_1l",
      "product_name": "Almarai Laban 1L",
      "store_id": "dubai_marina_01",
      "stock_quantity": 48,
      "expiry_date": "2026-10-19",
      "days_to_expiry": 2,
      "daily_sales_rate": 8.5,
      "projected_sell_through": 17,
      "units_at_risk": 31,
      "revenue_at_risk_aed": 248.00,
      "discount_pct": 25.0,
      "discounted_price_aed": 6.00,
      "revenue_recoverable_aed": 186.00,
      "evidence": {
        "data_source": "BigQuery incidents — 7-day velocity",
        "expiry_source": "AlloyDB inventory.expiry_date",
        "trigger_formula": "2 × 8.5 = 17 < 48 units in stock"
      },
      "status": "pending",
      "human_approval_required": true
    }
  ]
}
```

**No alerts:**
```json
{
  "perishable_alerts": []
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| store_id not found | NOT_FOUND | false |
| AlloyDB connection failed | DB_CONNECTION_ERROR | true |
| BigQuery velocity query failed | BIGQUERY_ERROR | true |
| No perishable items triggered | Returns empty array (not error) | — |

---

## 7. UNIT TESTS

```python
# TC-PULSE-06-U01: Trigger condition fires correctly
def test_perishable_discount_trigger():
    """
    Given: Laban 48 units, 2 days expiry, 8.5 units/day rate
    When: execute_perishable_discount called
    Then: Alert generated (2 × 8.5 = 17 < 48 → triggered)
    """

# TC-PULSE-06-U02: Trigger condition NOT met — no alert
def test_perishable_discount_no_trigger():
    """
    Given: Milk 10 units, 3 days expiry, 5 units/day rate
    When: execute_perishable_discount called
    Then: No alert (3 × 5 = 15 > 10 → not triggered)
    """

# TC-PULSE-06-U03: Correct discount tier — 2 days
def test_perishable_discount_tier_2days():
    """
    Given: Item expiring in exactly 2 days
    When: execute_perishable_discount called
    Then: discount_pct=25.0
    """

# TC-PULSE-06-U04: Correct discount tier — 1 day
def test_perishable_discount_tier_1day():
    """
    Given: Item expiring in exactly 1 day
    When: execute_perishable_discount called
    Then: discount_pct=40.0
    """

# TC-PULSE-06-U05: Correct discount tier — 3 days
def test_perishable_discount_tier_3days():
    """
    Given: Item expiring in exactly 3 days
    When: execute_perishable_discount called
    Then: discount_pct=15.0
    """

# TC-PULSE-06-U06: discounted_price_aed calculation correct
def test_perishable_discount_price_calculation():
    """
    Given: Original price AED 8.00, discount 25%
    When: execute_perishable_discount called
    Then: discounted_price_aed = 8.00 × 0.75 = AED 6.00
    """

# TC-PULSE-06-U07: status always pending
def test_perishable_discount_always_pending():
    """
    Given: Any triggered item
    When: execute_perishable_discount called
    Then: status="pending", human_approval_required=True always
    """

# TC-PULSE-06-U08: Non-perishable items excluded
def test_perishable_discount_non_perishable_excluded():
    """
    Given: Store has perishable and non-perishable items
    When: execute_perishable_discount called
    Then: Only is_perishable=true items in alerts
    """

# TC-PULSE-06-U09: Items > 3 days not triggered
def test_perishable_discount_far_expiry():
    """
    Given: Item expiring in 7 days
    When: execute_perishable_discount called
    Then: No alert generated (>3 days away)
    """

# TC-PULSE-06-U10: revenue_recoverable <= revenue_at_risk
def test_perishable_discount_recoverable_bounded():
    """
    Given: Any triggered item
    When: execute_perishable_discount called
    Then: revenue_recoverable_aed <= revenue_at_risk_aed always
    """

# TC-PULSE-06-U11: trigger_formula shows actual numbers
def test_perishable_discount_evidence_formula():
    """
    Given: 2 days, 8.5 rate, 48 units
    When: execute_perishable_discount called
    Then: trigger_formula = "2 × 8.5 = 17 < 48 units in stock"
    """

# TC-PULSE-06-U12: Empty store — no alerts
def test_perishable_discount_no_perishables():
    """
    Given: Store with no perishable items
    When: execute_perishable_discount called
    Then: perishable_alerts=[] (not an error)
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-PULSE-06-I01: Real inventory + BQ velocity
def test_perishable_discount_real_data(db_session, bq_client):
    """
    Given: Perishable inventory seeded in PostgreSQL
           and velocity data seeded in BigQuery emulator
    When: execute_perishable_discount called
    Then: Correctly triggers for items matching the condition
    """

# TC-PULSE-06-I02: No velocity data → zero rate
def test_perishable_discount_no_velocity(db_session, bq_client):
    """
    Given: Perishable item with no incidents in BigQuery
    When: execute_perishable_discount called
    Then: daily_sales_rate=0, all units at risk, trigger fires
    """

# TC-PULSE-06-I03: After manager approval, ARIA surfaces discount
def test_perishable_discount_aria_surfaces(db_session):
    """
    Given: Perishable alert approved → discount_active=True in inventory
    When: ARIA calls check_stock for that product
    Then: check_stock returns discount_active=True in response
    Note: End-to-end perishable loop integration test
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 5 requests/minute per IP |
| **Scheduling** | Runs automatically every 6 hours via Cloud Scheduler |
| **Human in loop** | human_approval_required ALWAYS true — never auto-apply discount |
| **Timeout** | AlloyDB + BigQuery queries within 15 seconds total |
| **Retry** | On DB/BQ timeout: retry 3 times with exponential backoff |
| **Discount precision** | discounted_price_aed rounded to exactly 2 decimal places |
| **Latency SLA** | p95 < 10 seconds (multiple queries) |
| **Logging** | Log: store_id, alerts_generated, items_checked, latency_ms |
| **Audit** | All proposed discounts logged regardless of approval outcome |

---

*MIRA Retail · ARC v1.0 · SPEC-PULSE-06 v1.0*
