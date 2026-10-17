# SPEC-ARIA-03: build_cart
> MIRA Retail · ARC Project · ARIA CX Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `build_cart`  
**Agent:** ARIA (CX Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → AlloyDB  
**Purpose:** Build a grocery cart from AlloyDB inventory that matches the customer's goal, dietary preference, and budget. Returns a list of recommended items and flags any unavailable products.

**Why it exists:** Cart building is the core value of ARIA. Rather than the customer manually searching for each item, ARIA builds the entire cart from a single goal statement — filtered by dietary restrictions, optimised for budget, and scoped to what is physically available at the customer's store.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `goal` | string | Yes | Non-empty, max 500 chars |
| `dietary_preference` | enum | Yes | halal, vegetarian, vegan, none |
| `budget_aed` | float | Yes | > 0, <= 10000 |
| `household_size` | integer | Yes | 1–20 |
| `store_id` | string | Yes | Must exist in stores table |

**Example input:**
```json
{
  "goal": "weekly groceries",
  "dietary_preference": "halal",
  "budget_aed": 300.00,
  "household_size": 4,
  "store_id": "dubai_marina_01"
}
```

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate all inputs
        → Validate goal length, dietary enum, budget range, store_id exists

Step 2: Call Gemini 1.5 Flash to map goal to grocery categories
        → "weekly groceries" → [dairy, grains, halal_meat, vegetables, fruits, beverages]
        → "biryani ingredients" → [grains, halal_meat, condiments, vegetables]
        → Restrict to 8 allowed categories only

Step 3: Query AlloyDB inventory for each category
        → SELECT * FROM inventory
          WHERE store_id = $1
          AND category = ANY($2)
          AND dietary_flags ILIKE '%' || $3 || '%'  (if halal/vegetarian/vegan)
          AND stock_quantity > 0
          ORDER BY price_aed ASC

Step 4: Select items for cart
        → Pick representative items per category based on household_size
        → Household multiplier: 1-2 persons=1x, 3-4=2x, 5+=3x
        → Flag items with stock_quantity = 0 as unavailable

Step 5: Calculate total
        → total_aed = SUM(item.price_aed * item.quantity)

Step 6: Return BuildCartResponse
        → items: list of available CartItemResponse
        → items_unavailable: list of products found in category but out of stock
        → total_aed: sum
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| goal not empty | len(strip(goal)) >= 1 | VALIDATION_ERROR |
| goal max length | len(goal) <= 500 | VALIDATION_ERROR |
| dietary_preference valid | halal, vegetarian, vegan, none | VALIDATION_ERROR |
| budget_aed positive | > 0 | VALIDATION_ERROR |
| budget_aed max | <= 10000 | VALIDATION_ERROR |
| household_size range | 1–20 | VALIDATION_ERROR |
| store_id exists | Must exist in stores table | NOT_FOUND |

### Output sanity checks
| Check | Rule |
|-------|------|
| No non-grocery items | Categories restricted to 8 allowed only |
| Dietary respected | No non-halal items if dietary_preference=halal |
| total_aed correct | Must equal SUM(price_aed * quantity) |
| in_stock consistent | Items in items list must have in_stock=true |
| At least 1 result | If 0 items found, return empty items with explanation |
| No negative prices | price_aed > 0 for all items |

---

## 5. OUTPUTS

**Success response:**
```json
{
  "items": [
    {
      "product_id": "milk_almarai_2l",
      "product_name": "Almarai Full Fat Milk 2L",
      "quantity": 2,
      "price_aed": 12.00,
      "aisle_ref": "A2",
      "in_stock": true
    }
  ],
  "total_aed": 287.50,
  "items_unavailable": [
    {
      "product_id": "rice_brown_500g",
      "product_name": "Brown Rice 500g"
    }
  ]
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| Invalid dietary_preference | VALIDATION_ERROR | false |
| store_id not found | NOT_FOUND | false |
| AlloyDB connection failed | DB_CONNECTION_ERROR | true |
| No items found for goal | Returns empty items list | — |
| budget_aed <= 0 | VALIDATION_ERROR | false |
| Non-grocery category requested | VALIDATION_ERROR | false |

---

## 7. UNIT TESTS

**File:** `tests/unit/aria/test_build_cart.py`

```python
# TC-ARIA-03-U01: Happy path — weekly halal cart
def test_build_cart_weekly_halal():
    """
    Given: goal="weekly groceries", dietary="halal", budget=300, household=4
    When: build_cart called with mock DB returning 12 items
    Then: Returns items list, total_aed <= 300, all items have in_stock=true
    """

# TC-ARIA-03-U02: Dietary filter respected — no non-halal items
def test_build_cart_halal_filter():
    """
    Given: dietary_preference="halal"
    When: build_cart called
    Then: No item in response has dietary_flags NOT containing "halal"
    """

# TC-ARIA-03-U03: Unavailable items flagged correctly
def test_build_cart_unavailable_items():
    """
    Given: Brown rice has stock_quantity=0 in mock DB
    When: build_cart called for weekly groceries
    Then: Brown rice in items_unavailable, not in items list
    """

# TC-ARIA-03-U04: total_aed calculation correct
def test_build_cart_total_calculation():
    """
    Given: 3 items at AED 10, AED 20, AED 30 with quantities 1, 2, 1
    When: build_cart called
    Then: total_aed = 10 + 40 + 30 = 80.00
    """

# TC-ARIA-03-U05: Non-grocery goal rejected
def test_build_cart_non_grocery():
    """
    Given: goal="laptop and phone accessories"
    When: build_cart called
    Then: Returns VALIDATION_ERROR — non-grocery categories rejected
    """

# TC-ARIA-03-U06: Store not found
def test_build_cart_invalid_store():
    """
    Given: store_id="nonexistent_store"
    When: build_cart called
    Then: Returns NOT_FOUND error
    """

# TC-ARIA-03-U07: Household size affects quantities
def test_build_cart_household_quantity():
    """
    Given: household_size=1 vs household_size=4 for same goal
    When: build_cart called twice
    Then: Quantities higher for household_size=4
    """

# TC-ARIA-03-U08: Empty store — no items
def test_build_cart_empty_store():
    """
    Given: Store with no inventory
    When: build_cart called
    Then: Returns items=[], items_unavailable=[], total_aed=0
    """
```

---

## 8. INTEGRATION TESTS

**File:** `tests/integration/test_aria_tools_integration.py`

```python
# TC-ARIA-03-I01: Real DB query builds cart
def test_build_cart_real_db(db_session):
    """
    Given: Inventory seeded with 50 MIRA Retail products
    When: build_cart queries PostgreSQL container
    Then: Returns at least 5 items for weekly groceries goal
    """

# TC-ARIA-03-I02: Dietary filter works on real data
def test_build_cart_halal_real_db(db_session):
    """
    Given: Mix of halal and non-halal products in DB
    When: build_cart called with dietary_preference=halal
    Then: All returned items have halal in dietary_flags
    """

# TC-ARIA-03-I03: total_aed matches DB prices
def test_build_cart_total_matches_db(db_session):
    """
    Given: Known prices in seeded inventory
    When: build_cart called
    Then: total_aed matches sum of prices from DB
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 30 requests/minute per IP |
| **Timeout** | AlloyDB query must complete within 5 seconds |
| **Retry** | On DB timeout: retry up to 3 times with exponential backoff |
| **Logging** | Log: store_id, dietary_preference, items_returned, total_aed, latency_ms |
| **Latency SLA** | p95 < 5 seconds (multiple DB queries) |
| **Category restriction** | Hard-coded allowed list checked before any DB query |

---

*MIRA Retail · ARC v1.0 · SPEC-ARIA-03 v1.0*
