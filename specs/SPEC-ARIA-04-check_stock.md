# SPEC-ARIA-04: check_stock
> MIRA Retail · ARC Project · ARIA CX Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `check_stock`  
**Agent:** ARIA (CX Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → AlloyDB  
**Purpose:** Check real-time stock availability for a specific product at a specific store. Returns quantity on hand, aisle reference, and alternative stores if the item is unavailable.

**Why it exists:** Inventory changes constantly. An item may appear in the product catalog but be out of stock. ARIA must verify each cart item before confirming it to the customer — checking stock prevents promising items that cannot be fulfilled.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `product_id` | string | Yes | Non-empty, must exist in inventory |
| `store_id` | string | Yes | Non-empty, must exist in stores |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate inputs
        → product_id and store_id non-empty
        → Both must exist in AlloyDB

Step 2: Query AlloyDB inventory
        → SELECT stock_quantity, aisle_ref
          FROM inventory
          WHERE product_id = $1 AND store_id = $2

Step 3: Determine availability
        → available = stock_quantity > 0

Step 4: If unavailable → find alternative stores
        → SELECT store_id, store_name, stock_quantity
          FROM inventory i
          JOIN stores s ON i.store_id = s.store_id
          WHERE i.product_id = $1
          AND i.stock_quantity > 0
          AND i.store_id != $2
          ORDER BY stock_quantity DESC
          LIMIT 3

Step 5: Return CheckStockResponse
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| product_id not empty | len(strip(id)) >= 1 | VALIDATION_ERROR |
| store_id not empty | len(strip(id)) >= 1 | VALIDATION_ERROR |
| product exists | Must exist in inventory table | NOT_FOUND |
| store exists | Must exist in stores table | NOT_FOUND |

### Output sanity checks
| Check | Rule |
|-------|------|
| quantity non-negative | stock_quantity >= 0 |
| aisle_ref present if available | If available=true, aisle_ref must be non-null |
| aisle_ref null if unavailable | If available=false, aisle_ref=null |
| alternative_stores only if unavailable | If available=true, alternative_stores=[] |
| distance_km positive | distance_km >= 0 for all alternatives |

---

## 5. OUTPUTS

```json
{
  "product_id": "rice_brown_500g",
  "available": false,
  "quantity": 0,
  "aisle_ref": null,
  "alternative_stores": [
    {
      "store_id": "jbr_01",
      "store_name": "MIRA JBR",
      "quantity": 45,
      "distance_km": 1.2
    }
  ]
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| product_id not found | NOT_FOUND | false |
| store_id not found | NOT_FOUND | false |
| DB connection failed | DB_CONNECTION_ERROR | true |
| Query timeout | TIMEOUT | true |

---

## 7. UNIT TESTS

```python
# TC-ARIA-04-U01: Item in stock
def test_check_stock_in_stock():
    """
    Given: product has stock_quantity=45, aisle_ref="B3"
    When: check_stock called
    Then: available=True, quantity=45, aisle_ref="B3", alternative_stores=[]
    """

# TC-ARIA-04-U02: Item out of stock with alternatives
def test_check_stock_out_of_stock_with_alternatives():
    """
    Given: product stock=0 at store A, stock=20 at store B
    When: check_stock called for store A
    Then: available=False, alternative_stores contains store B
    """

# TC-ARIA-04-U03: Item out of stock no alternatives
def test_check_stock_no_alternatives():
    """
    Given: product out of stock at all stores
    When: check_stock called
    Then: available=False, alternative_stores=[]
    """

# TC-ARIA-04-U04: Product not found
def test_check_stock_product_not_found():
    """
    Given: product_id="nonexistent"
    When: check_stock called
    Then: Returns NOT_FOUND error
    """

# TC-ARIA-04-U05: aisle_ref null when out of stock
def test_check_stock_aisle_null_when_unavailable():
    """
    Given: product stock=0
    When: check_stock called
    Then: aisle_ref=null in response
    """

# TC-ARIA-04-U06: Max 3 alternative stores returned
def test_check_stock_max_alternatives():
    """
    Given: Product in stock at 5 other stores
    When: check_stock called
    Then: alternative_stores has exactly 3 entries
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-ARIA-04-I01: Real inventory query
def test_check_stock_real_db(db_session):
    """
    Given: Inventory seeded with known stock levels
    When: check_stock queries PostgreSQL container
    Then: Returns correct stock_quantity from DB
    """

# TC-ARIA-04-I02: Alternative stores from real DB
def test_check_stock_alternatives_real_db(db_session):
    """
    Given: Product out of stock at store A, in stock at store B
    When: check_stock for store A
    Then: store B appears in alternative_stores
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 60 requests/minute per IP |
| **Timeout** | AlloyDB query within 2 seconds |
| **Retry** | DB timeout: retry 3 times with exponential backoff |
| **Latency SLA** | p95 < 1 second (single DB query) |
| **Logging** | Log: product_id, store_id, available, alternatives_count, latency_ms |

---

*MIRA Retail · ARC v1.0 · SPEC-ARIA-04 v1.0*
