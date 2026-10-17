# SPEC-ARIA-02: get_customer_context
> MIRA Retail · ARC Project · ARIA CX Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `get_customer_context`  
**Agent:** ARIA (CX Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → AlloyDB  
**Purpose:** Retrieve the customer's profile and last 3 orders from AlloyDB. Provides ARIA with the context needed to build a personalised cart — dietary preference, budget, household size, and purchase history.

**Why it exists:** Without customer context, ARIA builds a generic cart. With it, ARIA knows to filter halal, stay within the customer's usual budget, and reference what they ordered last time.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `customer_id` | string | Yes | Non-empty, max 100 chars, alphanumeric + underscore |

**Example input:**
```json
{
  "customer_id": "sarah_123"
}
```

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate customer_id
        → Strip whitespace
        → Check non-empty and max length
        → Validate format: alphanumeric + underscore only

Step 2: Query AlloyDB customer_profiles table
        → SELECT * FROM customer_profiles WHERE customer_id = $1
        → If no row found → return 404 NOT_FOUND error

Step 3: Query AlloyDB orders table for last 3 orders
        → SELECT DISTINCT product items FROM orders
          WHERE customer_id = $1
          ORDER BY created_at DESC
          LIMIT 3
        → Flatten JSONB items array to list of {product_id, product_name, last_ordered}

Step 4: Validate retrieved data
        → dietary_preference must be in allowed enum
        → weekly_budget_aed must be > 0
        → household_size must be 1–20

Step 5: Return CustomerContextResponse
        → Log retrieval to Cloud Logging
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| customer_id not empty | len(strip(id)) >= 1 | VALIDATION_ERROR |
| customer_id max length | len(id) <= 100 | VALIDATION_ERROR |
| customer_id format | Alphanumeric + underscore only | VALIDATION_ERROR |
| customer exists | Must exist in customer_profiles | NOT_FOUND |

### Output sanity checks
| Check | Rule |
|-------|------|
| dietary_preference valid | Must be: halal, vegetarian, vegan, none |
| weekly_budget_aed positive | Must be > 0 |
| household_size in range | Must be 1–20 |
| last_orders max 3 | Never return more than 3 items |
| last_ordered format | Must be valid ISO date |

---

## 5. OUTPUTS

**Success response:**
```json
{
  "customer_id": "sarah_123",
  "name": "Sarah Al Mansoori",
  "dietary_preference": "halal",
  "household_size": 4,
  "weekly_budget_aed": 300.00,
  "preferred_store": "dubai_marina_01",
  "last_orders": [
    {
      "product_id": "rice_basmati_2kg",
      "product_name": "Basmati Rice 2kg",
      "last_ordered": "2026-10-10"
    }
  ]
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| customer_id empty | VALIDATION_ERROR | false |
| customer_id not found | NOT_FOUND | false |
| AlloyDB connection failed | DB_CONNECTION_ERROR | true |
| AlloyDB query timeout | TIMEOUT | true |
| Invalid dietary_preference in DB | INTERNAL_ERROR | false |
| Auth token missing | AUTH_ERROR | false |
| Rate limit exceeded | RATE_LIMIT_EXCEEDED | true |

---

## 7. UNIT TESTS

**File:** `tests/unit/aria/test_get_customer_context.py`  
**Marker:** `@pytest.mark.unit`  
**Dependencies mocked:** AlloyDB client

```python
# TC-ARIA-02-U01: Happy path — full customer profile returned
def test_get_customer_context_success():
    """
    Given: customer_id="sarah_123" exists in mock DB
    When: get_customer_context called
    Then: Returns full profile with dietary_preference, budget, last_orders
    """

# TC-ARIA-02-U02: Customer not found returns 404
def test_get_customer_context_not_found():
    """
    Given: customer_id="unknown_999" not in DB
    When: get_customer_context called
    Then: Returns error_code=NOT_FOUND, retry_suggested=False
    """

# TC-ARIA-02-U03: Empty customer_id rejected
def test_get_customer_context_empty_id():
    """
    Given: customer_id=""
    When: get_customer_context called
    Then: Returns error_code=VALIDATION_ERROR
    """

# TC-ARIA-02-U04: Last orders capped at 3
def test_get_customer_context_orders_capped():
    """
    Given: Customer has 10 orders in DB
    When: get_customer_context called
    Then: last_orders contains exactly 3 items, most recent first
    """

# TC-ARIA-02-U05: Customer with no orders
def test_get_customer_context_no_orders():
    """
    Given: New customer with no orders
    When: get_customer_context called
    Then: Returns profile with last_orders=[]
    """

# TC-ARIA-02-U06: DB connection failure handled
def test_get_customer_context_db_failure(mock_alloydb):
    """
    Given: AlloyDB raises connection error
    When: get_customer_context called
    Then: Returns error_code=DB_CONNECTION_ERROR, retry_suggested=True
    """

# TC-ARIA-02-U07: Invalid format customer_id rejected
def test_get_customer_context_invalid_format():
    """
    Given: customer_id="sarah; DROP TABLE customers;"
    When: get_customer_context called
    Then: Returns error_code=VALIDATION_ERROR
    """

# TC-ARIA-02-U08: weekly_budget_aed always positive
def test_get_customer_context_budget_positive():
    """
    Given: Customer profile in DB has weekly_budget_aed=250
    When: get_customer_context called
    Then: weekly_budget_aed=250.0 (positive float)
    """
```

---

## 8. INTEGRATION TESTS

**File:** `tests/integration/test_alloydb_client.py`  
**Marker:** `@pytest.mark.integration`  
**Dependencies:** PostgreSQL Testcontainer

```python
# TC-ARIA-02-I01: Real DB query returns customer
def test_get_customer_context_real_db(db_session):
    """
    Given: customer_profiles seeded with sarah_123
    When: get_customer_context queries PostgreSQL container
    Then: Returns correct profile from real DB
    """

# TC-ARIA-02-I02: Transactional isolation between tests
def test_get_customer_context_isolation(db_session):
    """
    Given: Test inserts a customer row
    When: Test completes
    Then: Row is rolled back, not visible to next test
    """

# TC-ARIA-02-I03: Last 3 orders from real DB
def test_get_customer_context_orders_from_db(db_session):
    """
    Given: 5 orders seeded for sarah_123 with different timestamps
    When: get_customer_context queries DB
    Then: Returns exactly 3 most recent orders
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 60 requests/minute per IP |
| **Timeout** | AlloyDB query must complete within 3 seconds |
| **Retry** | On DB timeout: retry up to 3 times with exponential backoff |
| **Caching** | Customer profile may be cached in-memory for 60 seconds per session |
| **Logging** | Log: customer_id, latency_ms, orders_returned, status |
| **Latency SLA** | p95 < 2 seconds |
| **Data privacy** | Never log customer name or email in plain text |

---

*MIRA Retail · ARC v1.0 · SPEC-ARIA-02 v1.0*
