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

> **v1.1 — graceful degradation + personalization.** The ±20% price rule is a
> *preference with a fallback*, not a hard gate: real inventory may have no
> in-band substitute for an arbitrary product, and the system must still behave
> sensibly for inputs it did not choose (a judge may pick any product). Dietary
> rules remain a HARD filter and are never relaxed. Purchase history is used to
> personalize the choice.

```
Step 1: Validate inputs (product_id, store_id, dietary_preference, max_price_aed)
        → customer_id is OPTIONAL; when present, used for personalization

Step 2: Fetch the original product (price, category, text)
        → price band: floor = price × 0.80, ceiling = min(max_price, price × 1.20)

Step 3: Semantic candidate search (AlloyDB AI ScaNN / TF-IDF in mock)
        → cosine similarity over product text
        → HARD filters: store_id match, stock_quantity > 0,
          dietary_flags contains dietary_preference, product_id != original
        → Do NOT hard-filter on price here — gather candidates, score below

Step 4: Load purchase history (if customer_id given)
        → last_orders product_ids = history_set

Step 5: Rank candidates with a tiered score:
        Tier 1 (best): in price band (floor..ceiling) AND in history
        Tier 2:        in price band
        Tier 3:        out of band but dietary-safe + in stock (history boosts)
        Within a tier, higher cosine similarity wins.

Step 6: Build the result based on the chosen tier:
        → Tier 1/2  → in_band=true, offered as substitute;
          reason notes "you've ordered this before" when from history
        → Tier 3    → in_band=false, out_of_price_range=true, offered as an
          OPTION for the customer to decide (do not silently swap)
        → no candidate at all (nothing dietary-safe + in stock) →
          substitute_product_id=null, event_type set (see Step 7)

Step 7: Operational signal when no substitute exists
        → substitution_event = "new" | "recurring" based on whether this
          product has prior unavailability for this store (so the store
          manager / PULSE can act). Always safe: never violates dietary rules.

Step 8: Return SuggestSubstitutionResponse
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

**Substitute found, in price band (Tier 1 — from purchase history):**
```json
{
  "substitute_product_id": "rice_basmati_2kg",
  "name": "Basmati Rice 2kg",
  "price_aed": 11.00,
  "similarity_score": 0.87,
  "reason": "Similar grain product, matches halal preference — and you've ordered it before",
  "in_stock": true,
  "in_band": true,
  "out_of_price_range": false,
  "from_purchase_history": true,
  "substitution_event": null
}
```

**Substitute found, but outside the ±20% band (Tier 3 — offered as an option):**
```json
{
  "substitute_product_id": "rice_basmati_5kg",
  "name": "India Gate Basmati Rice 5kg",
  "price_aed": 45.00,
  "similarity_score": 0.71,
  "reason": "Closest halal grain in stock, but priced higher than your original — up to you",
  "in_stock": true,
  "in_band": false,
  "out_of_price_range": true,
  "from_purchase_history": false,
  "substitution_event": null
}
```

**No substitute found (operational signal for the store manager):**
```json
{
  "substitute_product_id": null,
  "name": null,
  "price_aed": null,
  "similarity_score": 0.0,
  "reason": "No suitable in-stock alternative — flagged to the store team",
  "in_stock": false,
  "in_band": false,
  "out_of_price_range": false,
  "from_purchase_history": false,
  "substitution_event": "new"
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
