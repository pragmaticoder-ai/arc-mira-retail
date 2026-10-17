-- ════════════════════════════════════════════════════════════════════
-- ARC — BigQuery schema (analytics bridge)
-- Source of truth: DATA_MODEL.md §2
-- Dataset: arc_dataset · Region: asia-southeast1
-- ════════════════════════════════════════════════════════════════════

-- ── Main bridge: ARIA writes, PULSE reads ───────────────────────────
CREATE TABLE IF NOT EXISTS arc_dataset.incidents (
    session_id              STRING NOT NULL,
    customer_id             STRING,
    store_id                STRING,
    timestamp               TIMESTAMP,

    items_ordered           JSON,   -- [{product_id, product_name, quantity, price_aed}]
    items_unavailable       JSON,   -- [{product_id, product_name}]
    substitutions_offered   JSON,   -- [{original_product_id, substitute_product_id, accepted}]

    promotion_id            STRING,
    promotion_saving_aed    FLOAT64,

    cart_total_aed          FLOAT64,
    budget_aed              FLOAT64,

    session_sentiment       STRING,   -- positive | neutral | negative
    order_placed            BOOL,
    abandonment_reason      STRING    -- null if order placed
)
PARTITION BY DATE(timestamp)
CLUSTER BY store_id, session_sentiment;

-- ── Inventory change audit log ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS arc_dataset.inventory_log (
    log_id          STRING NOT NULL,
    product_id      STRING,
    store_id        STRING,
    event_type      STRING,    -- stockout | restock | adjustment
    quantity_before INTEGER,
    quantity_after  INTEGER,
    logged_at       TIMESTAMP
)
PARTITION BY DATE(logged_at)
CLUSTER BY store_id, event_type;

-- ── Promotion effectiveness log ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS arc_dataset.promotion_log (
    log_id              STRING NOT NULL,
    promotion_id        STRING,
    customer_id         STRING,
    store_id            STRING,
    cart_before_aed     FLOAT64,
    cart_after_aed      FLOAT64,
    saving_aed          FLOAT64,
    converted           BOOL,
    logged_at           TIMESTAMP
)
PARTITION BY DATE(logged_at)
CLUSTER BY promotion_id;

-- ── BigQuery ML demand forecast (run after seed data loads) ─────────
CREATE OR REPLACE MODEL arc_dataset.demand_forecast
OPTIONS(
    model_type         = 'ARIMA_PLUS',
    time_series_timestamp_col = 'timestamp',
    time_series_data_col      = 'incident_count',
    time_series_id_col        = 'product_id',
    forecast_horizon   = 7,
    data_frequency     = 'daily'
) AS
SELECT
    TIMESTAMP_TRUNC(timestamp, DAY) AS timestamp,
    product_id,
    COUNT(*) AS incident_count
FROM (
    SELECT timestamp,
           JSON_VALUE(item, '$.product_id') AS product_id
    FROM arc_dataset.incidents,
    UNNEST(JSON_QUERY_ARRAY(items_unavailable)) AS item
)
GROUP BY 1, 2;
