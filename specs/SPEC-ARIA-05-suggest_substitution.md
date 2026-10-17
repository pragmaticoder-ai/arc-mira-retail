# SPEC-ARIA-05: suggest_substitution
> MIRA Retail · ARC Project · ARIA CX Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `suggest_substitution`  
**Agent:** ARIA (CX Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → AlloyDB AI (ScaNN)  
**Purpose:** When a product is out of stock, find the most semantically similar in-stock alternative using AlloyDB AI vector search. Respects dietary restrictions and price constraints.

**Why it exists:** Simply saying "item unavailable" loses the customer. A good substitution maintains the customer's shopping momentum and prevents cart abandonment — which is exactly what PULSE tracks as revenue at risk.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `product_id` | string | Yes | Must exist in inventory |
| `store_id` | string | Yes | Must exist in stores |
| `dietary_preference` | enum | Yes | halal, vegetarian, vegan, none |
| `max_price_aed` | float | Yes | > 0 |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate inputs
        → All fields required and valid

Step 2: Fetch embedding for the unavailable product
        → SELECT embedding FROM inventory
          WHERE product_id = $1
        → If no embedding → generate via AlloyDB AI on the fly

Step 3: Run ScaNN vector similarity search
        → SELECT product_id, product_name, price_aed,
                 1 - (embedding <=> $1) AS similarity
          FROM inventory
          WHERE store_id = $2
          AND stock_quantity > 0
          AND price_aed <= $3
          AND dietary_flags ILIKE '%' || $4 || '%'
          AND product_id != $5  -- exclude the original product
          ORDER BY embedding <=> $1
          LIMIT 1

Step 4: If no result found
        → Return null substitute with similarity_score=0.0

Step 5: Generate plain-language reason
        → Call Gemini Flash to generate human-readable explanation
          e.g. "Similar grain product, same dietary category, comparable price"

Step 6: Return SuggestSubstitutionResponse
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| product_id exists | Must exist in inventory | NOT_FOUND |
| store_id exists | Must exist in stores | NOT_FOUND |
| dietary_preference valid | halal, vegetarian, vegan, none | VALIDATION_ERROR |
| max_price_aed positive | > 0 | VALIDATION_ERROR |

### Output sanity checks
| Check | Rule |
|-------|------|
| Substitute not same as original | substitute_product_id != input product_id |
| Substitute in stock | in_stock must be true |
| Dietary respected | Substitute must match dietary_preference |
| Price within range | price_aed <= max_price_aed |
| Similarity valid range | 0.0 <= similarity_score <= 1.0 |
| Reason non-empty | If substitute found, reason must be non-empty |

---

## 5. OUTPUTS

**Substitute found:**
```json
{
  "substitute_product_id": "rice_basmati_2kg",
  "name": "Basmati Rice 2kg",
  "price_aed": 18.00,
  "similarity_score": 0.87,
  "reason": "Similar grain product, same halal category, comparable price",
  "in_stock": true
}
```

**No substitute found:**
```json
{
  "substitute_product_id": null,
  "name": null,
  "price_aed": null,
  "similarity_score": 0.0,
  "reason": "No suitable substitution found within price range",
  "in_stock": false
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| product_id not found | NOT_FOUND | false |
| store_id not found | NOT_FOUND | false |
| No embedding for product | INTERNAL_ERROR | true |
| AlloyDB AI search failed | DB_CONNECTION_ERROR | true |
| No substitute found | Returns null result (not an error) | — |

---

## 7. UNIT TESTS

```python
# TC-ARIA-05-U01: Substitute found with high similarity
def test_suggest_substitution_found():
    """
    Given: Brown rice out of stock, basmati rice available at AED 18
    When: suggest_substitution called with max_price=22, dietary=halal
    Then: Returns basmati rice with similarity_score > 0.7
    """

# TC-ARIA-05-U02: No substitute within price range
def test_suggest_substitution_price_too_low():
    """
    Given: All similar products cost more than max_price_aed
    When: suggest_substitution called
    Then: Returns null substitute with similarity_score=0.0
    """

# TC-ARIA-05-U03: Dietary filter respected
def test_suggest_substitution_dietary_filter():
    """
    Given: Non-halal substitute would be highest similarity
    When: suggest_substitution called with dietary=halal
    Then: Non-halal substitute not returned
    """

# TC-ARIA-05-U04: Original product excluded from results
def test_suggest_substitution_excludes_original():
    """
    Given: Original product is somehow back in stock
    When: suggest_substitution called
    Then: Original product_id not in substitute_product_id
    """

# TC-ARIA-05-U05: similarity_score in valid range
def test_suggest_substitution_score_range():
    """
    Given: Any valid substitution search
    When: suggest_substitution called
    Then: 0.0 <= similarity_score <= 1.0 always
    """

# TC-ARIA-05-U06: Product not found
def test_suggest_substitution_product_not_found():
    """
    Given: product_id="nonexistent"
    When: suggest_substitution called
    Then: Returns NOT_FOUND error
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-ARIA-05-I01: Vector search on real PostgreSQL
def test_suggest_substitution_real_vector_search(db_session):
    """
    Given: Inventory seeded with text embeddings (mock vector as text)
    When: suggest_substitution queries PostgreSQL container
    Then: Returns a result without error
    Note: Full ScaNN search tested against AlloyDB in staging only
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 60 requests/minute per IP |
| **Timeout** | Vector search + Gemini reason must complete within 5 seconds |
| **Retry** | On AlloyDB timeout: retry once |
| **Latency SLA** | p95 < 3 seconds |
| **Logging** | Log: product_id, substitute_found, similarity_score, latency_ms |

---

*MIRA Retail · ARC v1.0 · SPEC-ARIA-05 v1.0*
