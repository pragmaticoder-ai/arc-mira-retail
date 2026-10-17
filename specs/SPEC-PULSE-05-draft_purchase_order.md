# SPEC-PULSE-05: draft_purchase_order
> MIRA Retail · ARC Project · PULSE OPS Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `draft_purchase_order`  
**Agent:** PULSE (OPS Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → AlloyDB  
**Purpose:** Create a pending purchase order in AlloyDB for manager review. PULSE never approves orders — it always creates them in "pending" status and waits for explicit manager approval.

**Why it exists:** The operational intelligence is complete only when it produces an actionable output. A PO draft with full context — product, quantity, urgency, justification, and business impact — gives Ahmed everything he needs to make a one-click decision.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `product_id` | string | Yes | Must exist in inventory |
| `store_id` | string | Yes | Must exist in stores |
| `quantity` | integer | Yes | 1–10000 |
| `urgency` | enum | Yes | low, medium, high, critical |
| `justification` | string | Yes | Non-empty, max 1000 chars |
| `revenue_at_risk_aed` | float | Yes | >= 0 |
| `revenue_recoverable_aed` | float | Yes | >= 0 |
| `evidence_summary` | string | Yes | Non-empty, max 500 chars |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate all inputs

Step 2: Idempotency check
        → Check if pending PO exists for same product+store in last 24 hours
        → If exists: return existing PO (no duplicate)

Step 3: Lookup supplier for product
        → SELECT supplier_id FROM replenishment_schedule
          WHERE product_id = $1 AND store_id = $2

Step 4: Generate PO ID
        → Format: PO-{YEAR}-{SEQUENCE_NUMBER}

Step 5: INSERT into AlloyDB purchase_orders
        → status = "pending"
        → human_approval_required = true (ALWAYS)
        → created_by = "PULSE"

Step 6: Return DraftPurchaseOrderResponse
        → Include all PO details
        → human_approval_required ALWAYS true
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| product_id exists | In inventory | NOT_FOUND |
| store_id exists | In stores | NOT_FOUND |
| quantity range | 1–10000 | VALIDATION_ERROR |
| urgency valid | low, medium, high, critical | VALIDATION_ERROR |
| justification not empty | len >= 1 | VALIDATION_ERROR |
| justification max length | <= 1000 | VALIDATION_ERROR |
| revenue_at_risk | >= 0 | VALIDATION_ERROR |
| evidence_summary not empty | len >= 1 | VALIDATION_ERROR |

### Output sanity checks
| Check | Rule |
|-------|------|
| status always "pending" | Must never be "approved" on creation |
| human_approval_required | ALWAYS true — never false |
| created_by = "PULSE" | Never a human name |
| po_id non-empty | Must be generated unique ID |
| created_at accurate | Must be current UTC timestamp |
| Duplicate check | Same product+store within 24h → return existing PO |

---

## 5. OUTPUTS

```json
{
  "po_id": "PO-2026-0042",
  "product_id": "rice_brown_500g",
  "product_name": "Brown Rice 500g",
  "quantity": 120,
  "urgency": "critical",
  "justification": "23 customer incidents in 48 hours...",
  "revenue_at_risk_aed": 2961.00,
  "revenue_recoverable_aed": 3200.00,
  "evidence_summary": "BigQuery incidents (23 rows, Oct 14-16)...",
  "status": "pending",
  "human_approval_required": true,
  "created_at": "2026-10-17T09:32:00Z"
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| product_id not found | NOT_FOUND | false |
| Duplicate PO in 24h | Returns existing PO (not error) | — |
| DB connection failed | DB_CONNECTION_ERROR | true |
| quantity out of range | VALIDATION_ERROR | false |

---

## 7. UNIT TESTS

```python
# TC-PULSE-05-U01: PO created successfully
def test_draft_po_success():
    """
    Given: Valid product, store, quantity=120, urgency=critical
    When: draft_purchase_order called
    Then: Returns PO with status="pending", human_approval_required=True
    """

# TC-PULSE-05-U02: status always pending
def test_draft_po_always_pending():
    """
    Given: Any valid inputs
    When: draft_purchase_order called
    Then: status="pending" — never "approved" or "rejected"
    """

# TC-PULSE-05-U03: human_approval_required always true
def test_draft_po_approval_required():
    """
    Given: Any valid inputs
    When: draft_purchase_order called
    Then: human_approval_required=True — never False
    """

# TC-PULSE-05-U04: Idempotency — duplicate within 24h
def test_draft_po_duplicate():
    """
    Given: PO already created for same product+store within 24h
    When: draft_purchase_order called again
    Then: Returns existing po_id (no new PO created)
    """

# TC-PULSE-05-U05: created_by always PULSE
def test_draft_po_created_by():
    """
    Given: Any valid inputs
    When: draft_purchase_order called
    Then: created_by="PULSE" in DB record
    """

# TC-PULSE-05-U06: Quantity out of range rejected
def test_draft_po_invalid_quantity():
    """
    Given: quantity=0 or quantity=99999
    When: draft_purchase_order called
    Then: Returns VALIDATION_ERROR
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-PULSE-05-I01: Real PO insertion
def test_draft_po_real_db(db_session):
    """
    Given: Product and store seeded in PostgreSQL container
    When: draft_purchase_order called
    Then: Row created in purchase_orders table with status=pending
    """

# TC-PULSE-05-I02: Idempotency real DB
def test_draft_po_idempotency_real_db(db_session):
    """
    Given: PO already in DB for product+store
    When: draft_purchase_order called again within 24h
    Then: Only 1 row exists in purchase_orders for this product+store
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 5 requests/minute per IP (write operation) |
| **Idempotency** | Same product+store within 24h = return existing PO |
| **Human in loop** | human_approval_required ALWAYS true — enforced at DB and API level |
| **Timeout** | AlloyDB write within 5 seconds |
| **Retry** | On DB timeout: retry 3 times |
| **Audit** | All POs permanently retained for audit trail |
| **Latency SLA** | p95 < 3 seconds |
| **Logging** | Log: po_id, product_id, urgency, revenue_at_risk, latency_ms |

---

*MIRA Retail · ARC v1.0 · SPEC-PULSE-05 v1.0*
