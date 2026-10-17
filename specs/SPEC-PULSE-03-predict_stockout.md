# SPEC-PULSE-03: predict_stockout
> MIRA Retail · ARC Project · PULSE OPS Agent
> Version 1.0 | Status: Draft

---

## 1. OVERVIEW

**Function:** `predict_stockout`  
**Agent:** PULSE (OPS Agent)  
**Layer:** Tool function → Cloud Run → FastAPI → BigQuery ML  
**Purpose:** Use BigQuery ML ARIMA_PLUS model to forecast when a product will next run out of stock. Only surfaces predictions with confidence >= 0.70.

**Why it exists:** Root cause analysis tells you why something went wrong. Prediction tells you what will go wrong next. PULSE combining both makes it genuinely proactive — not just reacting to past stockouts but preventing future ones.

---

## 2. INPUTS

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `product_id` | string | Yes | Must exist in inventory |
| `store_id` | string | Yes | Must exist in stores |
| `forecast_days` | integer | No | 1–30, default 7 |

---

## 3. STEP BY STEP LOGIC

```
Step 1: Validate inputs

Step 2: Query current stock level from AlloyDB
        → SELECT stock_quantity FROM inventory
          WHERE product_id = $1 AND store_id = $2

Step 3: Calculate daily consumption rate from BigQuery
        → Query incidents table for last 30 days of order data
        → daily_rate = total_units_ordered / days_in_period

Step 4: Call BigQuery ML forecast
        → ML.FORECAST(MODEL arc_dataset.demand_forecast,
                      STRUCT($forecast_days AS horizon))
          WHERE product_id = $1

Step 5: Calculate days_until_stockout
        → days_until = stock_quantity / daily_consumption_rate

Step 6: Confidence check
        → If confidence < 0.70: return null predicted_stockout_date
          (still return confidence score so PULSE knows why it's not surfaced)

Step 7: Return PredictStockoutResponse
```

---

## 4. VALIDATIONS & SANITY CHECKS

### Input validations
| Check | Rule | Error code |
|-------|------|------------|
| product_id exists | In inventory | NOT_FOUND |
| store_id exists | In stores | NOT_FOUND |
| forecast_days range | 1–30 | VALIDATION_ERROR |

### Output sanity checks
| Check | Rule |
|-------|------|
| confidence range | 0.0 <= confidence <= 1.0 |
| Only surface >= 0.70 | predicted_stockout_date null if confidence < 0.70 |
| predicted_date future | Must be after current timestamp |
| days_until_stockout >= 0 | Cannot be negative |
| daily_consumption_rate > 0 | Must be positive |
| current_stock >= 0 | Non-negative |

---

## 5. OUTPUTS

**High confidence:**
```json
{
  "predicted_stockout_date": "2026-10-21",
  "days_until_stockout": 4,
  "confidence": 0.87,
  "current_stock": 12,
  "daily_consumption_rate": 3.2,
  "evidence": {
    "model": "BigQuery ML ARIMA_PLUS",
    "training_period": "Oct 1 - Oct 16 2026",
    "data_points_used": 480
  }
}
```

**Low confidence:**
```json
{
  "predicted_stockout_date": null,
  "days_until_stockout": null,
  "confidence": 0.52,
  "current_stock": 45,
  "daily_consumption_rate": 2.1,
  "evidence": {
    "model": "BigQuery ML ARIMA_PLUS",
    "training_period": "Oct 1 - Oct 16 2026",
    "data_points_used": 240
  }
}
```

---

## 6. ERROR CASES

| Scenario | Error code | retry_suggested |
|----------|------------|-----------------|
| BigQuery ML model not trained | BIGQUERY_ML_ERROR | false |
| BQ connection failed | BIGQUERY_ERROR | true |
| product_id not found | NOT_FOUND | false |
| confidence < 0.70 | Returns null date (not error) | — |

---

## 7. UNIT TESTS

```python
# TC-PULSE-03-U01: High confidence prediction surfaced
def test_predict_stockout_high_confidence():
    """
    Given: BQ ML returns confidence=0.87, 4 days to stockout
    When: predict_stockout called
    Then: predicted_stockout_date populated, days_until_stockout=4
    """

# TC-PULSE-03-U02: Low confidence — null date returned
def test_predict_stockout_low_confidence():
    """
    Given: BQ ML returns confidence=0.52
    When: predict_stockout called
    Then: predicted_stockout_date=null, confidence=0.52 returned
    """

# TC-PULSE-03-U03: confidence always in valid range
def test_predict_stockout_confidence_range():
    """
    Given: Any BQ ML response
    When: predict_stockout called
    Then: 0.0 <= confidence <= 1.0 always
    """

# TC-PULSE-03-U04: days_until_stockout non-negative
def test_predict_stockout_positive_days():
    """
    Given: stock=10, daily_rate=2.5
    When: predict_stockout called
    Then: days_until_stockout=4 (not negative)
    """

# TC-PULSE-03-U05: evidence block populated
def test_predict_stockout_evidence():
    """
    Given: BQ ML model trained on 30 days data
    When: predict_stockout called
    Then: evidence.model, training_period, data_points_used all non-empty
    """
```

---

## 8. INTEGRATION TESTS

```python
# TC-PULSE-03-I01: BigQuery emulator ML query
def test_predict_stockout_bq_emulator(bq_client):
    """
    Given: demand_forecast model created in BigQuery emulator
    When: predict_stockout queries emulator
    Then: Returns forecast response without error
    Note: Actual ML accuracy tested in staging vs real BigQuery ML
    """
```

---

## 9. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Specification |
|-------------|---------------|
| **Auth** | IAM Bearer token required |
| **Rate limit** | 10 requests/minute per IP (BigQuery ML heavy) |
| **Timeout** | BigQuery ML query within 30 seconds |
| **Retry** | On BQ timeout: retry once after 10 seconds |
| **Threshold** | confidence < 0.70 → suppress prediction (never show low-confidence to manager) |
| **Latency SLA** | p95 < 20 seconds (ML inference) |
| **Logging** | Log: product_id, confidence, days_until_stockout, latency_ms |

---

*MIRA Retail · ARC v1.0 · SPEC-PULSE-03 v1.0*
