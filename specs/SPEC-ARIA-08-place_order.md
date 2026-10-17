# SPEC-ARIA-08: place_order
> MIRA Retail · ARC Project · ARIA CX Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `place_order`  
**Agent:** ARIA (CX Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → AlloyDB  
**Purpose:** Write the confirmed customer order to AlloyDB. Only called after the customer gives explicit confirmation. Decrements inventory stock for each ordered item.

**Why it exists:** This is the transaction that creates revenue. It must be idempotent, accurate, and only execute on explicit human confirmation — never auto-triggered by ARIA without the customer saying yes.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `customer_id` | string | Yes | Must exist in customer_profiles |
| `store_id` | string | Yes | Must exist in stores |
| `cart` | array | Yes | Min 1 item |
| `promotion_id` | string | No | If provided, must exist in promotions |
| `total_aed` | float | Yes | > 0, must match cart sum |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate all inputs
        → customer_id, store_id exist
        → cart non-empty, all items valid
        → total_aed matches SUM(item.price_aed * item.quantity) ± AED 0.01

Step 2: Idempotency check
        → Check if order for same customer in last 60 seconds exists
        → If duplicate → return existing order_id (do not create new)

Step 3: Re-verify stock for all items
        → For each item: SELECT stock_quantity FROM inventory
          WHERE product_id = $1 AND store_id = $2
        → If any item stock_quantity < item.quantity → return VALIDATION_ERROR

Step 4: Begin AlloyDB transaction
        → INSERT INTO orders (customer_id, store_id, items, total_aed,
                              promotion_id, status)
          VALUES (...)
        → For each item:
          UPDATE inventory SET stock_quantity = stock_quantity - $quantity
          WHERE product_id = $1 AND store_id = $2

Step 5: Commit transaction
        → If any step fails → rollback all changes

Step 6: Calculate delivery window
        → Next available 2-hour slot starting from tomorrow morning

Step 7: Return PlaceOrderResponse
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| customer_id exists | Must exist in customer_profiles | NOT_FOUND |
| store_id exists | Must exist in stores | NOT_FOUND |
| cart not empty | len(cart) >= 1 | VALIDATION_ERROR |
| total_aed matches | Within ±AED 0.01 of SUM | VALIDATION_ERROR |
| total_aed positive | > 0 | VALIDATION_ERROR |
| promotion_id valid | If provided, must exist in promotions | NOT_FOUND |

### Output sanity checks
| Check | Rule |
|-------|------|
| status always "confirmed" | Must be "confirmed" on creation |
| order_id generated | Non-empty unique order ID |
| delivery_window future | Must be after current timestamp |
| Stock decremented | inventory.stock_quantity reduced for each item |
| Atomic transaction | Either all items decremented or none |

---

## 5. OUTPUTS

```json
{
  "order_id": "MR-2026-4821",
  "status": "confirmed",
  "total_aed": 272.00,
  "estimated_delivery_window": "Sat 18 Oct · 10:00–12:00"
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| customer_id not found | NOT_FOUND | false |
| Stock insufficient at order time | VALIDATION_ERROR | false |
| Duplicate order (60s window) | Returns existing order | — |
| Transaction rollback | DB_CONNECTION_ERROR | true |
| total_aed mismatch | VALIDATION_ERROR | false |

---

## 7. UNIT TESTS

```python
# TC-ARIA-08-U01: Happy path — order placed
def test_place_order_success():
    """
    Given: Valid cart, customer exists, all items in stock
    When: place_order called
    Then: Returns order_id, status="confirmed", delivery_window in future
    """

# TC-ARIA-08-U02: Idempotency — duplicate within 60s
def test_place_order_duplicate():
    """
    Given: Same customer places same order within 60 seconds
    When: place_order called twice
    Then: Second call returns same order_id as first (no duplicate created)
    """

# TC-ARIA-08-U03: total_aed mismatch rejected
def test_place_order_total_mismatch():
    """
    Given: total_aed=100 but cart items sum to AED 200
    When: place_order called
    Then: Returns VALIDATION_ERROR
    """

# TC-ARIA-08-U04: Stock decremented after order
def test_place_order_stock_decremented(mock_db):
    """
    Given: Product has stock_quantity=10, order quantity=2
    When: place_order called
    Then: stock_quantity becomes 8 in DB
    """

# TC-ARIA-08-U05: Atomic transaction — partial failure rolls back
def test_place_order_atomic(mock_db):
    """
    Given: First item decrements OK, second item DB error
    When: place_order called
    Then: First item stock_quantity NOT decremented (full rollback)
    """

# TC-ARIA-08-U06: Stock insufficient at order time
def test_place_order_insufficient_stock():
    """
    Given: Item had stock when cart built, now stock=0
    When: place_order called
    Then: Returns VALIDATION_ERROR (stock re-verified at order time)
    """

# TC-ARIA-08-U07: Delivery window is future date
def test_place_order_delivery_future():
    """
    Given: Any valid order
    When: place_order called
    Then: estimated_delivery_window is after current timestamp
    """

# TC-ARIA-08-U08: With promotion
def test_place_order_with_promotion():
    """
    Given: Valid promotion_id provided
    When: place_order called
    Then: Order stored with promotion_id, total reflects discount
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-ARIA-08-I01: Real DB order creation
def test_place_order_real_db(db_session):
    """
    Given: Customer and inventory seeded in PostgreSQL container
    When: place_order called
    Then: Order row created in orders table, stock decremented
    """

# TC-ARIA-08-I02: Rollback on failure
def test_place_order_rollback(db_session):
    """
    Given: DB error mid-transaction
    When: place_order fails
    Then: No order row created, stock unchanged
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 10 requests/minute per IP (write operation) |
| **Idempotency** | Same customer+cart within 60 seconds = no-op, return existing |
| **Atomicity** | Order insert + stock decrement in single transaction |
| **Timeout** | Transaction must complete within 10 seconds |
| **Retry** | No auto-retry on place_order (financial transaction) |
| **Latency SLA** | p95 < 5 seconds |
| **Logging** | Log: order_id, customer_id, total_aed, items_count, latency_ms |
| **Audit** | All orders permanently stored — never deleted |

---

*MIRA Retail · ARC v1.0 · SPEC-ARIA-08 v1.0*
