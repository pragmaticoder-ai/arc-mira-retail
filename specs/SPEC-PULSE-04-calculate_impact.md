# SPEC-PULSE-04: calculate_impact
> MIRA Retail · ARC Project · PULSE OPS Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `calculate_impact`  
**Agent:** PULSE (OPS Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → BigQuery  
**Purpose:** Calculate the business impact in AED of a confirmed stockout pattern — revenue already lost, revenue at risk if unresolved, and revenue recoverable if the manager approves the recommended purchase order today.

**Why it exists:** Ahmed is a business manager, not a data analyst. He needs numbers in AED before he can justify a decision. calculate_impact converts raw incident data into a clear financial case for action — always with the formula cited so he can verify it himself.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `product_id` | string | Yes | Must exist in inventory |
| `store_id` | string | Yes | Must exist in stores |
| `incident_count` | integer | Yes | >= 1 |
| `average_cart_aed` | float | Yes | > 0 |
| `abandonment_count` | integer | Yes | >= 0, <= incident_count |
| `days_to_next_delivery` | integer | Yes | >= 0 |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate inputs

Step 2: Calculate abandonment_rate
        → abandonment_rate = abandonment_count / incident_count

Step 3: Calculate revenue_lost_aed (historical — last 48 hours)
        → revenue_lost = incident_count × average_cart_aed
                         × abandonment_rate × MARGIN_PCT
        → MARGIN_PCT = 0.15 (15% gross margin assumption)

Step 4: Calculate revenue_at_risk_aed (next 7 days if unresolved)
        → daily_incident_rate = incident_count / 2  (per 48h period)
        → revenue_at_risk = daily_incident_rate × 7
                            × average_cart_aed × abandonment_rate × MARGIN_PCT

Step 5: Calculate revenue_recoverable_aed
        → Based on days_to_next_delivery:
          If PO approved today → delivers in lead_time_days
          revenue_recoverable = revenue_at_risk × (7 - lead_time_days) / 7

Step 6: Build calculation_basis plain-language string
        → "23 incidents × AED 220 avg cart × 0.22 abandonment rate × 0.15 margin = AED 847"

Step 7: Return CalculateImpactResponse with evidence block
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| product_id exists | In inventory | NOT_FOUND |
| store_id exists | In stores | NOT_FOUND |
| incident_count | >= 1 | VALIDATION_ERROR |
| average_cart_aed | > 0 | VALIDATION_ERROR |
| abandonment_count | >= 0 AND <= incident_count | VALIDATION_ERROR |
| days_to_next_delivery | >= 0 | VALIDATION_ERROR |

### Output sanity checks
| Check | Rule |
|-------|------|
| revenue_lost non-negative | >= 0 |
| revenue_at_risk non-negative | >= 0 |
| revenue_recoverable <= at_risk | Cannot recover more than at risk |
| calculation_basis non-empty | Must show the formula |
| evidence.formula non-empty | Must be present |
| abandonment_rate valid | 0.0 <= rate <= 1.0 |

---

## 5. OUTPUTS

```json
{
  "revenue_lost_aed": 847.00,
  "revenue_at_risk_aed": 2961.00,
  "revenue_recoverable_aed": 3200.00,
  "calculation_basis": "23 incidents × AED 220 avg cart × 0.22 abandonment × 0.15 margin = AED 847",
  "evidence": {
    "incidents_used": 23,
    "average_cart_aed": 220.00,
    "abandonment_rate": 0.22,
    "formula": "incident_count × avg_cart_aed × abandonment_rate × margin_pct"
  }
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| abandonment_count > incident_count | VALIDATION_ERROR | false |
| average_cart_aed <= 0 | VALIDATION_ERROR | false |
| product_id not found | NOT_FOUND | false |

---

## 7. UNIT TESTS

```python
# TC-PULSE-04-U01: Correct revenue calculation
def test_calculate_impact_formula():
    """
    Given: incident_count=23, avg_cart=220, abandonment=5
    When: calculate_impact called
    Then: revenue_lost = 23 * 220 * (5/23) * 0.15 = AED 165
    Note: Tests exact formula application
    """

# TC-PULSE-04-U02: revenue_recoverable <= revenue_at_risk
def test_calculate_impact_recoverable_bounded():
    """
    Given: Any valid inputs
    When: calculate_impact called
    Then: revenue_recoverable_aed <= revenue_at_risk_aed always
    """

# TC-PULSE-04-U03: abandonment_rate calculation
def test_calculate_impact_abandonment_rate():
    """
    Given: incident_count=10, abandonment_count=3
    When: calculate_impact called
    Then: evidence.abandonment_rate = 0.30
    """

# TC-PULSE-04-U04: abandonment_count > incident_count rejected
def test_calculate_impact_invalid_abandonment():
    """
    Given: incident_count=5, abandonment_count=10
    When: calculate_impact called
    Then: Returns VALIDATION_ERROR
    """

# TC-PULSE-04-U05: calculation_basis plain language
def test_calculate_impact_basis_readable():
    """
    Given: Any valid inputs
    When: calculate_impact called
    Then: calculation_basis is human-readable string with actual numbers
    """

# TC-PULSE-04-U06: Zero abandonments
def test_calculate_impact_zero_abandonment():
    """
    Given: abandonment_count=0
    When: calculate_impact called
    Then: revenue_lost_aed=0 (no lost revenue if all were substituted)
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-PULSE-04-I01: Impact matches seed data
def test_calculate_impact_matches_seed(db_session):
    """
    Given: Known incident data seeded in BigQuery emulator
    When: calculate_impact called
    Then: Output matches expected calculation from seed data
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 20 requests/minute per IP |
| **Timeout** | Calculation within 3 seconds (no external calls) |
| **Evidence mandatory** | formula and calculation_basis must always be present |
| **Latency SLA** | p95 < 2 seconds (pure calculation, minimal DB) |
| **Logging** | Log: product_id, revenue_lost, revenue_at_risk, latency_ms |
| **Precision** | All AED values rounded to 2 decimal places |

---

*MIRA Retail · ARC v1.0 · SPEC-PULSE-04 v1.0*
