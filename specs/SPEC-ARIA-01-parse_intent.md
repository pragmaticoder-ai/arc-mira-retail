# SPEC-ARIA-01: parse_intent
> MIRA Retail · ARC Project · ARIA CX Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `parse_intent`  
**Agent:** ARIA (CX Agent)  
**Layer:** Tool function → Cloud Run → FastAPI  
**Purpose:** Extract structured shopping intent from a customer's raw natural language message. This is always the first tool ARIA calls at the start of a new session.

**Why it exists:** Customers express their needs in natural language — *"I need halal groceries for the week, family of 4, under AED 300"*. ARIA cannot call `build_cart` without structured parameters. `parse_intent` bridges natural language to structured data.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `customer_message` | string | Yes | Min 1 char, Max 1000 chars, non-empty after strip |

**Example input:**
```json
{
  "customer_message": "I need groceries for the week, family of 4, halal, under AED 300"
}
```

---

## 3. STEP BY STEP LOGIC

```
Step 1: Receive customer_message
        → Strip leading/trailing whitespace
        → Validate length (1–1000 chars)
        → Sanitize: reject if contains SQL injection patterns or script tags

Step 2: Call Gemini 1.5 Flash with structured extraction prompt
        → Prompt instructs model to extract:
           goal, dietary_preference, budget_aed, household_size, urgency
        → Model responds in JSON only

Step 3: Parse Gemini response
        → Validate JSON structure
        → Apply defaults for missing fields:
           - dietary_preference → "none" if not mentioned
           - household_size → null if not mentioned
           - budget_aed → null if not mentioned
           - urgency → "normal" if not mentioned

Step 4: Validate extracted values against allowed enums
        → dietary_preference must be: halal | vegetarian | vegan | none
        → urgency must be: normal | urgent

Step 5: Return structured ParseIntentResponse
        → Log extraction result to Cloud Logging
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| Message not empty | len(strip(message)) >= 1 | VALIDATION_ERROR |
| Message not too long | len(message) <= 1000 | VALIDATION_ERROR |
| No SQL injection | message must not contain: DROP, SELECT *, INSERT, DELETE, --, ; | VALIDATION_ERROR |
| No script tags | message must not contain: `<script>`, `javascript:` | VALIDATION_ERROR |

### Output sanity checks
| Check | Rule |
|-------|------|
| dietary_preference is valid | Must be one of: halal, vegetarian, vegan, none |
| urgency is valid | Must be one of: normal, urgent |
| budget_aed positive | If present, must be > 0 |
| household_size positive | If present, must be between 1–20 |
| goal is non-empty | If Gemini returns empty goal, default to "grocery shopping" |

---

## 5. OUTPUTS

**Success response:**
```json
{
  "goal": "weekly groceries",
  "dietary_preference": "halal",
  "budget_aed": 300.00,
  "household_size": 4,
  "urgency": "normal"
}
```

**Partial response (fields not mentioned by customer):**
```json
{
  "goal": "milk",
  "dietary_preference": "none",
  "budget_aed": null,
  "household_size": null,
  "urgency": "urgent"
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| Empty message | VALIDATION_ERROR | false |
| Message > 1000 chars | VALIDATION_ERROR | false |
| SQL/script injection detected | VALIDATION_ERROR | false |
| Gemini API timeout (>5s) | TIMEOUT | true |
| Gemini returns invalid JSON | INTERNAL_ERROR | true |
| Auth token missing/invalid | AUTH_ERROR | false |
| Rate limit exceeded | RATE_LIMIT_EXCEEDED | true |

---

## 7. UNIT TESTS

**File:** `tests/unit/aria/test_parse_intent.py`  
**Marker:** `@pytest.mark.unit`  
**Dependencies mocked:** Gemini API

```python
# TC-ARIA-01-U01: Happy path — full intent extraction
def test_parse_intent_full_message():
    """
    Given: "I need halal groceries for the week, family of 4, under AED 300"
    When: parse_intent is called
    Then: Returns goal="weekly groceries", dietary_preference="halal",
          budget_aed=300.0, household_size=4, urgency="normal"
    """

# TC-ARIA-01-U02: Dietary preference extraction — vegetarian
def test_parse_intent_vegetarian():
    """
    Given: "I need vegetarian food for 2 people"
    When: parse_intent is called
    Then: dietary_preference="vegetarian", household_size=2
    """

# TC-ARIA-01-U03: Urgency extraction
def test_parse_intent_urgent():
    """
    Given: "I need milk urgently right now"
    When: parse_intent is called
    Then: urgency="urgent", goal="milk"
    """

# TC-ARIA-01-U04: Missing fields default correctly
def test_parse_intent_partial_message():
    """
    Given: "I need some groceries"
    When: parse_intent is called
    Then: goal="groceries", dietary_preference="none",
          budget_aed=None, household_size=None, urgency="normal"
    """

# TC-ARIA-01-U05: Empty message rejected
def test_parse_intent_empty_message():
    """
    Given: customer_message=""
    When: parse_intent is called
    Then: Raises ValidationError with error_code=VALIDATION_ERROR
    """

# TC-ARIA-01-U06: Message too long rejected
def test_parse_intent_message_too_long():
    """
    Given: customer_message="a" * 1001
    When: parse_intent is called
    Then: Raises ValidationError with error_code=VALIDATION_ERROR
    """

# TC-ARIA-01-U07: SQL injection rejected
def test_parse_intent_sql_injection():
    """
    Given: customer_message="SELECT * FROM inventory; DROP TABLE orders;"
    When: parse_intent is called
    Then: Raises ValidationError with error_code=VALIDATION_ERROR
    """

# TC-ARIA-01-U08: Gemini timeout handled
def test_parse_intent_gemini_timeout(mock_gemini):
    """
    Given: Gemini API times out after 5 seconds
    When: parse_intent is called
    Then: Returns error with error_code=TIMEOUT, retry_suggested=True
    """

# TC-ARIA-01-U09: Budget in different formats
def test_parse_intent_budget_formats():
    """
    Given: "my budget is three hundred dirhams"
    When: parse_intent is called
    Then: budget_aed=300.0 (Gemini normalizes to float)
    """

# TC-ARIA-01-U10: Arabic/mixed language message
def test_parse_intent_mixed_language():
    """
    Given: "أريد groceries for the week, halal, AED 200"
    When: parse_intent is called
    Then: dietary_preference="halal", budget_aed=200.0
    """
```

---

## 8. INTEGRATION TESTS

**File:** `tests/integration/test_aria_tools_integration.py`  
**Marker:** `@pytest.mark.integration`  
**Dependencies:** Real FastAPI app running locally, Gemini API (or mock)

```python
# TC-ARIA-01-I01: HTTP endpoint returns 200
def test_parse_intent_endpoint_success():
    """
    Given: Valid request to POST /tools/parse-intent
    When: FastAPI app handles the request
    Then: Returns 200 with valid ParseIntentResponse
    """

# TC-ARIA-01-I02: Auth header required
def test_parse_intent_no_auth():
    """
    Given: Request with no Authorization header
    When: POST /tools/parse-intent called in production mode
    Then: Returns 401 Unauthorized
    """

# TC-ARIA-01-I03: Rate limit enforced
def test_parse_intent_rate_limit():
    """
    Given: 61 requests sent within 1 minute from same IP
    When: 61st request hits /tools/parse-intent
    Then: Returns 429 Too Many Requests with Retry-After header
    """

# TC-ARIA-01-I04: Structured log emitted
def test_parse_intent_logs_structured():
    """
    Given: Successful parse_intent call
    When: Function completes
    Then: Structured JSON log contains agent, tool, latency_ms, status fields
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required. Bypass in ENVIRONMENT=development |
| **Rate limit** | 60 requests/minute per IP |
| **Timeout** | Gemini call must complete within 5 seconds |
| **Retry** | On Gemini timeout: retry once with 1s backoff |
| **Logging** | Log: tool name, customer_id (if available), latency_ms, status |
| **Latency SLA** | p95 < 3 seconds end-to-end |
| **Input sanitization** | Strip whitespace, reject injection patterns before any processing |

---

*MIRA Retail · ARC v1.0 · SPEC-ARIA-01 v1.0*
