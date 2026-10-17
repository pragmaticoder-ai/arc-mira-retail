# SPEC-ARIA-09: log_session
> MIRA Retail · ARC Project · ARIA CX Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `log_session`  
**Agent:** ARIA (CX Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → BigQuery  
**Purpose:** Write the complete session summary to the BigQuery incidents table. This is the bridge that connects ARIA to PULSE — every customer friction point becomes operational intelligence.

**Why it exists:** Without this function, the customer experience and store operations remain disconnected. log_session is the architectural core of ARC — it is what makes the system a loop rather than two separate tools. It must always be called, even if no order was placed.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `session_id` | string (UUID) | Yes | Valid UUID format |
| `customer_id` | string | Yes | Non-empty |
| `store_id` | string | Yes | Non-empty |
| `items_ordered` | array | Yes | Can be empty |
| `items_unavailable` | array | Yes | Can be empty |
| `substitutions` | array | Yes | Can be empty |
| `promotion_id` | string | No | Nullable |
| `promotion_saving_aed` | float | Yes | >= 0 |
| `cart_total_aed` | float | Yes | >= 0 |
| `budget_aed` | float | Yes | >= 0 |
| `sentiment` | enum | Yes | positive, neutral, negative |
| `order_placed` | boolean | Yes | |
| `abandonment_reason` | string | No | Nullable, required if order_placed=false |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate all inputs
        → session_id must be valid UUID
        → sentiment must be valid enum
        → promotion_saving_aed >= 0
        → cart_total_aed >= 0

Step 2: Idempotency check
        → If session_id already exists in BigQuery → return existing log (no-op)

Step 3: Write to BigQuery via streaming insert
        → Insert row into arc_dataset.incidents
        → Include all fields including evidence arrays

Step 4: Retry on failure
        → On BigQuery write error: retry up to 3 times with exponential backoff
        → After 3 failures: log error to Cloud Logging, return error response
        → IMPORTANT: log_session failure must NOT prevent customer
          seeing their order confirmation

Step 5: Return LogSessionResponse
        → session_id, logged=True, timestamp
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| session_id UUID format | Must match UUID regex | VALIDATION_ERROR |
| sentiment valid | positive, neutral, negative | VALIDATION_ERROR |
| promotion_saving_aed | >= 0 | VALIDATION_ERROR |
| cart_total_aed | >= 0 | VALIDATION_ERROR |
| budget_aed | >= 0 | VALIDATION_ERROR |
| order_placed bool | Must be true or false | VALIDATION_ERROR |

### Output sanity checks
| Check | Rule |
|-------|------|
| Idempotent | Duplicate session_id → return logged=True, no duplicate row |
| Write within 5s | BigQuery insert must complete in 5 seconds |
| logged=True on success | Must confirm the write |
| timestamp accurate | timestamp must be current UTC time |

---

## 5. OUTPUTS

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "logged": true,
  "timestamp": "2026-10-17T10:32:00Z"
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| Invalid UUID | VALIDATION_ERROR | false |
| BigQuery write failed after 3 retries | BIGQUERY_WRITE_ERROR | true |
| Duplicate session_id | Returns existing log (no error) | — |
| Invalid sentiment | VALIDATION_ERROR | false |

---

## 7. UNIT TESTS

```python
# TC-ARIA-09-U01: Happy path — session logged
def test_log_session_success():
    """
    Given: Valid session with order placed
    When: log_session called
    Then: Returns logged=True, timestamp is current UTC
    """

# TC-ARIA-09-U02: Idempotency — duplicate session_id
def test_log_session_duplicate():
    """
    Given: session_id already exists in BigQuery
    When: log_session called again with same session_id
    Then: Returns logged=True, no duplicate row created
    """

# TC-ARIA-09-U03: Session without order
def test_log_session_no_order():
    """
    Given: order_placed=False, abandonment_reason="budget exceeded"
    When: log_session called
    Then: Returns logged=True (abandonment sessions are important to log)
    """

# TC-ARIA-09-U04: Empty arrays valid
def test_log_session_empty_arrays():
    """
    Given: items_ordered=[], items_unavailable=[], substitutions=[]
    When: log_session called
    Then: Returns logged=True (empty arrays are valid)
    """

# TC-ARIA-09-U05: BigQuery failure retried
def test_log_session_bigquery_retry(mock_bq):
    """
    Given: BigQuery raises error on first 2 attempts, succeeds on 3rd
    When: log_session called
    Then: Returns logged=True after 3 attempts
    """

# TC-ARIA-09-U06: Invalid UUID rejected
def test_log_session_invalid_uuid():
    """
    Given: session_id="not-a-uuid"
    When: log_session called
    Then: Returns VALIDATION_ERROR
    """

# TC-ARIA-09-U07: Invalid sentiment rejected
def test_log_session_invalid_sentiment():
    """
    Given: sentiment="happy"
    When: log_session called
    Then: Returns VALIDATION_ERROR
    """

# TC-ARIA-09-U08: BQ failure does not block order confirmation
def test_log_session_failure_non_blocking(mock_bq):
    """
    Given: BigQuery consistently fails
    When: log_session called after place_order
    Then: Returns BIGQUERY_WRITE_ERROR but place_order already succeeded
    Note: Validates that these are separate calls with no shared transaction
    """
```

---

## 8. INTEGRATION TESTS

**File:** `tests/integration/test_bridge.py`

```python
# TC-ARIA-09-I01: Write to BigQuery emulator
def test_log_session_bigquery_emulator(bq_client):
    """
    Given: BigQuery emulator running in Docker
    When: log_session writes to emulator
    Then: Row visible in arc_dataset.incidents via SELECT
    """

# TC-ARIA-09-I02: PULSE can read what ARIA wrote
def test_bridge_aria_writes_pulse_reads(bq_client):
    """
    Given: log_session writes session with items_unavailable
    When: detect_patterns queries same BigQuery emulator
    Then: Pattern detected from ARIA's write
    Note: This is the end-to-end bridge integration test
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 60 requests/minute per IP |
| **Idempotency** | session_id is primary key — duplicate writes are no-ops |
| **Retry** | BigQuery write: retry 3 times with exponential backoff |
| **Non-blocking** | log_session failure must not affect order confirmation |
| **Timeout** | BigQuery write within 5 seconds per attempt |
| **Latency SLA** | p95 < 5 seconds (including retry) |
| **Logging** | Log: session_id, order_placed, items_unavailable_count, latency_ms |
| **Retention** | BigQuery data retained for 90 days minimum |

---

*MIRA Retail · ARC v1.0 · SPEC-ARIA-09 v1.0*
