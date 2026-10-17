# SPEC-PULSE-01: detect_patterns
> MIRA Retail · ARC Project · PULSE OPS Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `detect_patterns`  
**Agent:** PULSE (OPS Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → BigQuery  
**Purpose:** Query the BigQuery incidents table (written by ARIA) to detect products with repeated stockout incidents, ranked by revenue impact. This is always the first tool PULSE calls.

**Why it exists:** PULSE has no intelligence without raw signal. detect_patterns transforms ARIA's session logs into ranked operational alerts — identifying which products are causing the most customer friction and business loss.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `store_id` | string | Yes | Non-empty |
| `hours` | integer | No | 1–168, default 48 |
| `min_incidents` | integer | No | 1–100, default 5 |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate inputs

Step 2: Query BigQuery incidents table
        → SELECT
            product_id,
            COUNT(*) as incident_count,
            SUM(cart_total_aed * 0.15) as estimated_revenue_lost,
            MIN(timestamp) as first_seen,
            MAX(timestamp) as last_seen,
            COUNTIF(order_placed = false) as abandonment_count,
            ARRAY_AGG(session_id LIMIT 3) as sample_session_ids,
            SAFE_DIVIDE(
              COUNTIF(EXISTS(SELECT 1 FROM UNNEST(substitutions) s WHERE s.accepted)),
              COUNT(*)
            ) as substitution_acceptance_rate
          FROM arc_dataset.incidents,
          UNNEST(items_unavailable) as unavailable_item
          WHERE store_id = $1
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL $2 HOUR)
          GROUP BY product_id
          HAVING incident_count >= $3
          ORDER BY estimated_revenue_lost DESC

Step 3: Map product_ids to product names
        → Query AlloyDB or cache for product names

Step 4: Identify peak hour per product
        → Subquery: find hour with most incidents per product

Step 5: Return DetectPatternsResponse
        → Sorted by estimated_revenue_lost_aed DESC
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| store_id not empty | len(strip(id)) >= 1 | VALIDATION_ERROR |
| hours in range | 1 <= hours <= 168 | VALIDATION_ERROR |
| min_incidents in range | 1 <= min_incidents <= 100 | VALIDATION_ERROR |

### Output sanity checks
| Check | Rule |
|-------|------|
| Results sorted by revenue | estimated_revenue_lost_aed must be descending |
| incident_count matches | Must equal actual BigQuery count |
| estimated_revenue_lost positive | >= 0 |
| substitution_acceptance_rate valid | 0.0 <= rate <= 1.0 |
| sample_session_ids valid UUIDs | Must be valid UUID format |
| Empty array valid | No patterns = return empty array (not error) |

---

## 5. OUTPUTS

```json
{
  "patterns": [
    {
      "product_id": "rice_brown_500g",
      "product_name": "Brown Rice 500g",
      "store_id": "dubai_marina_01",
      "incident_count": 23,
      "period_hours": 48,
      "estimated_revenue_lost_aed": 847.00,
      "peak_hour": "10:00-12:00",
      "abandonment_count": 5,
      "evidence": {
        "first_incident": "2026-10-14T10:32:00Z",
        "last_incident": "2026-10-16T11:14:00Z",
        "sample_session_ids": ["550e8400-..."],
        "substitution_acceptance_rate": 0.78
      }
    }
  ]
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| BigQuery connection failed | BIGQUERY_ERROR | true |
| Query timeout (>30s) | TIMEOUT | true |
| No patterns found | Returns empty patterns array | — |
| Invalid store_id | VALIDATION_ERROR | false |

---

## 7. UNIT TESTS

```python
# TC-PULSE-01-U01: Patterns detected and sorted by revenue
def test_detect_patterns_sorted():
    """
    Given: Mock BQ returns 3 products with revenues 847, 200, 50
    When: detect_patterns called
    Then: Returns patterns in descending revenue order: 847, 200, 50
    """

# TC-PULSE-01-U02: No patterns returns empty array
def test_detect_patterns_empty():
    """
    Given: No incidents in BigQuery for last 48 hours
    When: detect_patterns called
    Then: Returns patterns=[] (not an error)
    """

# TC-PULSE-01-U03: min_incidents threshold respected
def test_detect_patterns_threshold():
    """
    Given: Product A has 3 incidents, Product B has 7 incidents
    When: detect_patterns called with min_incidents=5
    Then: Only Product B in results
    """

# TC-PULSE-01-U04: abandonment_count accurate
def test_detect_patterns_abandonment():
    """
    Given: 10 sessions, 3 with order_placed=False
    When: detect_patterns called
    Then: abandonment_count=3 in pattern
    """

# TC-PULSE-01-U05: evidence block populated
def test_detect_patterns_evidence():
    """
    Given: Sessions with known timestamps and session_ids
    When: detect_patterns called
    Then: first_incident, last_incident, sample_session_ids all populated
    """

# TC-PULSE-01-U06: hours parameter filters correctly
def test_detect_patterns_hours_filter():
    """
    Given: Incidents from 3 days ago and 1 day ago
    When: detect_patterns called with hours=24
    Then: Only incidents from last 24 hours included
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-PULSE-01-I01: Real BigQuery emulator query
def test_detect_patterns_bigquery_emulator(bq_client):
    """
    Given: incidents table seeded in BigQuery emulator
    When: detect_patterns queries emulator
    Then: Returns correct patterns from real BQ query
    """

# TC-PULSE-01-I02: Bridge test — reads ARIA writes
def test_detect_patterns_reads_aria_sessions(bq_client):
    """
    Given: ARIA logged sessions via log_session to emulator
    When: detect_patterns runs on same emulator
    Then: Detects patterns from ARIA's sessions
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 10 requests/minute per IP (BigQuery heavy) |
| **Timeout** | BigQuery query within 30 seconds |
| **Retry** | On BQ timeout: retry once after 5 seconds |
| **Scheduling** | Also runs on 6-hour schedule via Cloud Scheduler |
| **Latency SLA** | p95 < 15 seconds (BigQuery aggregation) |
| **Logging** | Log: store_id, patterns_found, hours, latency_ms |

---

*MIRA Retail · ARC v1.0 · SPEC-PULSE-01 v1.0*
