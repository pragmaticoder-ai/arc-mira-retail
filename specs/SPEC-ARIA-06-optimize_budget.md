# SPEC-ARIA-06: optimize_budget
> MIRA Retail · ARC Project · ARIA CX Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `optimize_budget`  
**Agent:** ARIA (CX Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → Gemini reasoning  
**Purpose:** When a cart exceeds the customer's budget, intelligently trim or swap items to bring the total within the target. Explains every change made to the customer.

**Why it exists:** Customers set budgets and expect them to be respected. Rather than presenting an over-budget cart and asking the customer to figure out what to remove, ARIA handles it intelligently — removing the least impactful items and explaining each change.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `cart` | array | Yes | Min 1 item |
| `target_budget_aed` | float | Yes | > 0 |
| `dietary_preference` | enum | Yes | halal, vegetarian, vegan, none |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate inputs
        → Cart has at least 1 item
        → target_budget_aed > 0
        → All cart items have valid product_id, quantity > 0, price_aed > 0

Step 2: Calculate current total
        → current_total = SUM(item.price_aed * item.quantity)
        → If current_total <= target_budget_aed → return cart unchanged

Step 3: Calculate overage
        → overage = current_total - target_budget_aed

Step 4: Call Gemini 1.5 Flash to select optimisation strategy
        → Prompt: given cart items and overage, which items to reduce/remove
          with least impact on meal planning?
        → Strategy priority:
           1. Reduce quantity of premium items (e.g. 2x butter → 1x butter)
           2. Swap to cheaper brand in same category
           3. Remove lowest-priority item (snacks before staples)

Step 5: Apply changes
        → Remove or reduce items per Gemini recommendation
        → Recalculate total after each change
        → Stop when total <= target_budget_aed

Step 6: Validate result
        → new_total_aed must be <= target_budget_aed
        → new_total_aed must be >= target_budget_aed * 0.85
        → All dietary restrictions still respected
        → At least 1 item remains in cart

Step 7: Return OptimizeBudgetResponse
        → updated_cart, new_total_aed, changes_made
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| cart not empty | len(cart) >= 1 | VALIDATION_ERROR |
| target_budget positive | > 0 | VALIDATION_ERROR |
| all items valid | product_id non-empty, quantity >= 1, price_aed > 0 | VALIDATION_ERROR |
| dietary_preference valid | halal, vegetarian, vegan, none | VALIDATION_ERROR |

### Output sanity checks
| Check | Rule |
|-------|------|
| Budget met | new_total_aed <= target_budget_aed |
| Not over-trimmed | new_total_aed >= target_budget_aed * 0.85 |
| Cart not empty | len(updated_cart) >= 1 |
| Dietary maintained | No dietary violations introduced |
| Changes explained | len(changes_made) > 0 if any changes were made |
| Action valid | action must be: removed, reduced_quantity, swapped_brand |

---

## 5. OUTPUTS

```json
{
  "updated_cart": [
    {
      "product_id": "milk_almarai_2l",
      "product_name": "Almarai Full Fat Milk 2L",
      "quantity": 1,
      "price_aed": 12.00,
      "aisle_ref": "A2",
      "in_stock": true
    }
  ],
  "new_total_aed": 287.00,
  "changes_made": [
    {
      "action": "reduced_quantity",
      "product_name": "Almarai Full Fat Milk 2L",
      "saving_aed": 12.00
    }
  ]
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| Cart empty | VALIDATION_ERROR | false |
| target_budget <= 0 | VALIDATION_ERROR | false |
| Cannot reach budget (all essentials) | UNPROCESSABLE | false |
| Gemini reasoning failed | INTERNAL_ERROR | true |

---

## 7. UNIT TESTS

```python
# TC-ARIA-06-U01: Cart already within budget — no changes
def test_optimize_budget_already_within():
    """
    Given: Cart total AED 280, target AED 300
    When: optimize_budget called
    Then: Returns original cart unchanged, changes_made=[]
    """

# TC-ARIA-06-U02: Reduce quantity of one item
def test_optimize_budget_reduce_quantity():
    """
    Given: Cart total AED 320, target AED 300
    When: optimize_budget called
    Then: new_total_aed <= 300, at least one item has reduced quantity
    """

# TC-ARIA-06-U03: Result not over-trimmed
def test_optimize_budget_not_over_trimmed():
    """
    Given: Cart total AED 340, target AED 300
    When: optimize_budget called
    Then: new_total_aed >= 255 (85% of 300)
    """

# TC-ARIA-06-U04: Dietary maintained after optimization
def test_optimize_budget_dietary_maintained():
    """
    Given: Halal cart, target budget requires removal
    When: optimize_budget called
    Then: All remaining items still have halal dietary_flags
    """

# TC-ARIA-06-U05: Cart not emptied
def test_optimize_budget_cart_not_empty():
    """
    Given: Single item cart that exceeds budget
    When: optimize_budget called
    Then: Cart still has at least 1 item, UNPROCESSABLE if impossible
    """

# TC-ARIA-06-U06: changes_made explains all changes
def test_optimize_budget_changes_explained():
    """
    Given: 2 items removed from cart
    When: optimize_budget called
    Then: changes_made has 2 entries, one per change
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-ARIA-06-I01: Full optimization flow
def test_optimize_budget_full_flow():
    """
    Given: Cart with 10 items totaling AED 350, target AED 300
    When: optimize_budget called with Gemini mock
    Then: Returns cart with total <= AED 300
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 30 requests/minute per IP |
| **Timeout** | Gemini call within 5 seconds |
| **Retry** | On Gemini timeout: retry once |
| **Latency SLA** | p95 < 5 seconds |
| **Logging** | Log: original_total, target_budget, new_total, changes_count, latency_ms |

---

*MIRA Retail · ARC v1.0 · SPEC-ARIA-06 v1.0*
