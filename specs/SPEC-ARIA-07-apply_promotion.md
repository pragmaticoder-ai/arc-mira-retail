# SPEC-ARIA-07: apply_promotion
> MIRA Retail · ARC Project · ARIA CX Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `apply_promotion`  
**Agent:** ARIA (CX Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → AlloyDB  
**Purpose:** Check AlloyDB for applicable active promotions and apply the highest-value relevant one to the cart. Also surfaces perishable discounts approved by the store manager (discount_active=True).

**Why it exists:** Promotions drive conversion. Customers who see a relevant discount applied automatically feel the system is working for them. PULSE-approved perishable discounts also flow through this function — completing the closed loop.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `cart` | array | Yes | Min 1 item |
| `cart_total_aed` | float | Yes | > 0 |
| `dietary_preference` | enum | Yes | halal, vegetarian, vegan, none |
| `store_id` | string | Yes | Must exist in stores |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate inputs

Step 2: Query AlloyDB promotions table
        → SELECT * FROM promotions
          WHERE is_active = true
          AND valid_from <= NOW()
          AND valid_until >= NOW()
          AND (dietary_filter IS NULL OR dietary_filter = $1)
          AND min_cart_aed <= $2
          AND (max_uses IS NULL OR times_applied < max_uses)
          ORDER BY discount_pct DESC, discount_flat_aed DESC

Step 3: Also query inventory for discount_active items
        → SELECT product_id, price_aed, discount_active
          FROM inventory
          WHERE store_id = $1
          AND discount_active = true

Step 4: Select best applicable promotion
        → Pick promotion with highest AED value
        → Calculate discount_aed:
           If discount_pct: discount_aed = cart_total * (discount_pct / 100)
           If discount_flat: discount_aed = discount_flat_aed

Step 5: Apply promotion
        → new_total_aed = cart_total_aed - discount_aed
        → Increment promotions.times_applied + 1

Step 6: Return ApplyPromotionResponse
        → If no promotion found: promotion_applied=false, discount_aed=0
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| cart not empty | len(cart) >= 1 | VALIDATION_ERROR |
| cart_total_aed positive | > 0 | VALIDATION_ERROR |
| store_id exists | Must exist in stores | NOT_FOUND |
| dietary_preference valid | halal, vegetarian, vegan, none | VALIDATION_ERROR |

### Output sanity checks
| Check | Rule |
|-------|------|
| new_total positive | new_total_aed > 0 (promotion cannot make cart free) |
| discount_aed correct | If pct: discount = cart_total * pct/100 |
| new_total correct | new_total = cart_total - discount_aed |
| Promotion active | Only valid_from <= now <= valid_until promotions applied |
| Dietary respected | Promotion dietary_filter matches customer preference |
| times_applied incremented | promotions.times_applied +1 after application |

---

## 5. OUTPUTS

**Promotion applied:**
```json
{
  "promotion_applied": true,
  "promotion_id": "promo_halal_bundle_oct",
  "promotion_name": "Halal Family Bundle",
  "discount_aed": 15.00,
  "new_total_aed": 272.00,
  "reason": "Cart qualifies for Halal Family Bundle (min AED 250)"
}
```

**No promotion:**
```json
{
  "promotion_applied": false,
  "promotion_id": null,
  "promotion_name": null,
  "discount_aed": 0.0,
  "new_total_aed": 287.00,
  "reason": "No applicable promotions for this cart"
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| store_id not found | NOT_FOUND | false |
| DB connection failed | DB_CONNECTION_ERROR | true |
| Promotion expired | Returns no promotion (not error) | — |
| new_total would be <= 0 | UNPROCESSABLE | false |

---

## 7. UNIT TESTS

```python
# TC-ARIA-07-U01: Valid promotion applied
def test_apply_promotion_success():
    """
    Given: Cart AED 287, active promotion 15% off min AED 250
    When: apply_promotion called
    Then: discount_aed=43.05, new_total=243.95, promotion_applied=True
    """

# TC-ARIA-07-U02: No applicable promotion
def test_apply_promotion_none():
    """
    Given: Cart AED 100, promotion requires min AED 250
    When: apply_promotion called
    Then: promotion_applied=False, discount_aed=0, new_total unchanged
    """

# TC-ARIA-07-U03: Expired promotion not applied
def test_apply_promotion_expired():
    """
    Given: Promotion valid_until yesterday
    When: apply_promotion called
    Then: promotion_applied=False
    """

# TC-ARIA-07-U04: Dietary filter respected
def test_apply_promotion_dietary_filter():
    """
    Given: Promotion for vegetarian only, customer is halal
    When: apply_promotion called
    Then: promotion_applied=False (dietary mismatch)
    """

# TC-ARIA-07-U05: Highest value promotion selected
def test_apply_promotion_best_selected():
    """
    Given: Two valid promotions: 10% off and 15% off
    When: apply_promotion called
    Then: 15% promotion applied (higher value)
    """

# TC-ARIA-07-U06: times_applied incremented
def test_apply_promotion_increments_count(mock_db):
    """
    Given: Promotion with times_applied=5
    When: apply_promotion called and promotion applied
    Then: times_applied becomes 6 in DB
    """

# TC-ARIA-07-U07: Max uses limit respected
def test_apply_promotion_max_uses():
    """
    Given: Promotion with max_uses=100, times_applied=100
    When: apply_promotion called
    Then: promotion_applied=False (limit reached)
    """

# TC-ARIA-07-U08: Perishable discount_active surfaced
def test_apply_promotion_perishable_discount():
    """
    Given: inventory has discount_active=True for Laban
    When: apply_promotion called with Laban in cart
    Then: Discount surfaced in promotion reason
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-ARIA-07-I01: Real promotions query
def test_apply_promotion_real_db(db_session):
    """
    Given: Promotions seeded with active and expired promotions
    When: apply_promotion queries PostgreSQL container
    Then: Only active, valid promotions considered
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 60 requests/minute per IP |
| **Timeout** | AlloyDB queries within 3 seconds total |
| **Retry** | On DB timeout: retry 3 times |
| **Idempotency** | Applying same promotion twice in same session = no-op |
| **Latency SLA** | p95 < 2 seconds |
| **Logging** | Log: promotion_id, discount_aed, cart_total_before, latency_ms |

---

*MIRA Retail · ARC v1.0 · SPEC-ARIA-07 v1.0*
