# SPEC-PULSE-02: find_root_cause
> MIRA Retail · ARC Project · PULSE OPS Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `find_root_cause`  
**Agent:** PULSE (OPS Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → AlloyDB + BigQuery  
**Purpose:** Cross-reference a detected stockout pattern with AlloyDB replenishment schedule to identify why the stockout is occurring. Always returns a mandatory evidence block citing exact data sources.

**Why it exists:** Knowing a stockout happened is not enough. Ahmed needs to know WHY before he can fix it. find_root_cause converts a BigQuery pattern into an operational diagnosis with evidence the manager can verify independently.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `product_id` | string | Yes | Must exist in inventory |
| `store_id` | string | Yes | Must exist in stores |
| `peak_hour` | string | Yes | Format: HH:MM-HH:MM |
| `incident_count` | integer | Yes | >= 5 |
| `period_hours` | integer | Yes | 1–168 |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate inputs

Step 2: Query AlloyDB replenishment_schedule
        → SELECT delivery_day, delivery_time, quantity_per_delivery, lead_time_days
          FROM replenishment_schedule
          WHERE product_id = $1 AND store_id = $2

Step 3: Parse peak_hour into time window
        → e.g. "10:00-12:00" → peak_start=10:00, peak_end=12:00

Step 4: Calculate gap
        → Convert delivery_time to minutes from midnight
        → Convert peak_start to minutes from midnight
        → gap_hours = |peak_start - delivery_time| / 60
        → If delivery_time > peak_start: gap_hours = delivery arrives AFTER peak

Step 5: Determine root cause
        → If gap_hours >= 2: root_cause = "delivery_timing_mismatch"
        → If quantity_per_delivery < incident_count * 2: root_cause = "insufficient_order_quantity"
        → If no replenishment schedule found: root_cause = "unknown"

Step 6: Assign confidence level
        → High: clear pattern + matching schedule data
        → Medium: pattern found, partial schedule data
        → Low: incident count 5-9 or conflicting data

Step 7: Generate plain-language explanation + recommended action

Step 8: Return FindRootCauseResponse with mandatory evidence block
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| product_id exists | In inventory table | NOT_FOUND |
| store_id exists | In stores table | NOT_FOUND |
| peak_hour format | Regex: ^\d{2}:\d{2}-\d{2}:\d{2}$ | VALIDATION_ERROR |
| incident_count | >= 5 | VALIDATION_ERROR |
| period_hours | 1–168 | VALIDATION_ERROR |

### Output sanity checks
| Check | Rule |
|-------|------|
| confidence_level valid | High, Medium, Low only |
| evidence data_sources | Must contain >= 2 entries |
| gap_hours non-negative | >= 0 |
| explanation non-empty | Must be non-empty string |
| recommended_action non-empty | Must be non-empty string |
| root_cause valid | delivery_timing_mismatch, insufficient_order_quantity, supplier_delay, demand_spike, unknown |

---

## 5. OUTPUTS

```json
{
  "root_cause": "delivery_timing_mismatch",
  "confidence_level": "High",
  "explanation": "Delivery arrives Tuesday 14:00 but demand peaks Mon-Wed 10:00-12:00 — 4-hour supply gap",
  "evidence": {
    "delivery_day": "Tuesday",
    "delivery_time": "14:00",
    "demand_peak_window": "10:00-12:00",
    "gap_hours": 4,
    "data_sources": [
      "BigQuery incidents table: 23 rows, Oct 14-16 2026",
      "AlloyDB replenishment_schedule: store=dubai_marina_01, product=rice_brown_500g"
    ]
  },
  "recommended_action": "Switch to twice-weekly delivery, schedule morning arrival 06:00-08:00"
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| product_id not found | NOT_FOUND | false |
| No replenishment schedule | Returns root_cause="unknown" | — |
| AlloyDB connection failed | DB_CONNECTION_ERROR | true |
| Invalid peak_hour format | VALIDATION_ERROR | false |

---

## 7. UNIT TESTS

```python
# TC-PULSE-02-U01: Delivery timing mismatch detected
def test_find_root_cause_timing_mismatch():
    """
    Given: Delivery Tuesday 14:00, peak hour 10:00-12:00
    When: find_root_cause called
    Then: root_cause="delivery_timing_mismatch", gap_hours=4, confidence=High
    """

# TC-PULSE-02-U02: No schedule found → unknown
def test_find_root_cause_no_schedule():
    """
    Given: No replenishment_schedule row for product+store
    When: find_root_cause called
    Then: root_cause="unknown", confidence=Low
    """

# TC-PULSE-02-U03: Evidence block always populated
def test_find_root_cause_evidence_populated():
    """
    Given: Any valid root cause analysis
    When: find_root_cause called
    Then: evidence.data_sources has >= 2 entries
    """

# TC-PULSE-02-U04: Low confidence for borderline incidents
def test_find_root_cause_low_confidence():
    """
    Given: incident_count=5 (minimum threshold)
    When: find_root_cause called
    Then: confidence_level="Medium" or "Low"
    """

# TC-PULSE-02-U05: Invalid peak_hour format rejected
def test_find_root_cause_invalid_peak_hour():
    """
    Given: peak_hour="morning"
    When: find_root_cause called
    Then: Returns VALIDATION_ERROR
    """

# TC-PULSE-02-U06: recommended_action non-empty
def test_find_root_cause_action_provided():
    """
    Given: Any valid root cause
    When: find_root_cause called
    Then: recommended_action is non-empty actionable string
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-PULSE-02-I01: Real replenishment schedule query
def test_find_root_cause_real_db(db_session):
    """
    Given: replenishment_schedule seeded with Tuesday 14:00 delivery
    When: find_root_cause queries PostgreSQL container
    Then: Correctly identifies timing mismatch from real data
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 20 requests/minute per IP |
| **Timeout** | AlloyDB + calculation within 5 seconds |
| **Retry** | On DB timeout: retry 3 times |
| **Evidence mandatory** | data_sources must never be empty |
| **Latency SLA** | p95 < 3 seconds |
| **Logging** | Log: product_id, root_cause, confidence_level, latency_ms |

---

*MIRA Retail · ARC v1.0 · SPEC-PULSE-02 v1.0*
