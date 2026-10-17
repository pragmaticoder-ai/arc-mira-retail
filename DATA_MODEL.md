# DATA_MODEL.md — AlloyDB + BigQuery Schemas
> MIRA Retail · ARC v1.0

---

## 1. AlloyDB schema (operational data)

```sql
-- ════════════════════════════════════════
-- Extensions
-- ════════════════════════════════════════
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS google_ml_integration;

-- ════════════════════════════════════════
-- Stores
-- ════════════════════════════════════════
CREATE TABLE stores (
    store_id        VARCHAR(50) PRIMARY KEY,
    store_name      VARCHAR(200) NOT NULL,
    area            VARCHAR(100),
    city            VARCHAR(50) DEFAULT 'Dubai',
    address         TEXT,
    is_active       BOOLEAN DEFAULT true
);

-- ════════════════════════════════════════
-- Customer profiles
-- ════════════════════════════════════════
CREATE TABLE customer_profiles (
    customer_id         VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(100) NOT NULL,
    email               VARCHAR(100) UNIQUE,
    phone               VARCHAR(20),
    dietary_preference  VARCHAR(20) DEFAULT 'none'
                        CHECK (dietary_preference IN ('halal','vegetarian','vegan','none')),
    household_size      INTEGER DEFAULT 1,
    weekly_budget_aed   DECIMAL(10,2),
    preferred_store     VARCHAR(50) REFERENCES stores(store_id),
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- ════════════════════════════════════════
-- Suppliers
-- ════════════════════════════════════════
CREATE TABLE suppliers (
    supplier_id     VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_name   VARCHAR(200) NOT NULL,
    contact_email   VARCHAR(100),
    lead_time_days  INTEGER DEFAULT 2
);

-- ════════════════════════════════════════
-- Inventory (with AlloyDB AI vector embeddings)
-- ════════════════════════════════════════
CREATE TABLE inventory (
    product_id          VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name        VARCHAR(200) NOT NULL,
    category            VARCHAR(100),
    brand               VARCHAR(100),
    price_aed           DECIMAL(10,2) NOT NULL,
    dietary_flags       VARCHAR(200),   -- comma-separated: halal,vegetarian,vegan
    store_id            VARCHAR(50) NOT NULL REFERENCES stores(store_id),
    aisle_ref           VARCHAR(20),    -- e.g. "A3", "B12"
    stock_quantity      INTEGER DEFAULT 0,
    reorder_threshold   INTEGER DEFAULT 10,
    supplier_id         VARCHAR(36) REFERENCES suppliers(supplier_id),
    embedding           vector(768),    -- AlloyDB AI: ScaNN semantic search
    updated_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON inventory USING scann(embedding cosine) WITH (num_leaves=10);
CREATE INDEX ON inventory(store_id, category);
CREATE INDEX ON inventory(store_id, stock_quantity);

-- ════════════════════════════════════════
-- Orders
-- ════════════════════════════════════════
CREATE TABLE orders (
    order_id                VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id             VARCHAR(36) NOT NULL REFERENCES customer_profiles(customer_id),
    store_id                VARCHAR(50) NOT NULL REFERENCES stores(store_id),
    items                   JSONB NOT NULL,
    -- [{product_id, product_name, quantity, price_aed, substituted: bool}]
    total_aed               DECIMAL(10,2) NOT NULL,
    promotion_id            VARCHAR(36),
    promotion_saving_aed    DECIMAL(10,2) DEFAULT 0,
    status                  VARCHAR(20) DEFAULT 'confirmed'
                            CHECK (status IN ('confirmed','processing','delivered','cancelled')),
    delivery_window_start   TIMESTAMP,
    delivery_window_end     TIMESTAMP,
    created_at              TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON orders(customer_id);
CREATE INDEX ON orders(store_id, created_at);

-- ════════════════════════════════════════
-- Promotions
-- ════════════════════════════════════════
CREATE TABLE promotions (
    promotion_id        VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(200) NOT NULL,
    description         TEXT,
    category            VARCHAR(100),       -- applies to which product category
    dietary_filter      VARCHAR(20),        -- null = applies to all
    discount_pct        DECIMAL(5,2),       -- e.g. 15.00 = 15%
    discount_flat_aed   DECIMAL(10,2),      -- alternative: flat discount
    min_cart_aed        DECIMAL(10,2) DEFAULT 0,
    max_uses            INTEGER,            -- null = unlimited
    times_applied       INTEGER DEFAULT 0,
    valid_from          TIMESTAMP NOT NULL,
    valid_until         TIMESTAMP NOT NULL,
    is_active           BOOLEAN DEFAULT true
);

-- ════════════════════════════════════════
-- Replenishment schedules
-- ════════════════════════════════════════
CREATE TABLE replenishment_schedule (
    schedule_id             VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id                VARCHAR(50) NOT NULL REFERENCES stores(store_id),
    product_id              VARCHAR(36) NOT NULL REFERENCES inventory(product_id),
    supplier_id             VARCHAR(36) REFERENCES suppliers(supplier_id),
    delivery_day            VARCHAR(20),    -- Monday, Tuesday...
    delivery_time           TIME,
    quantity_per_delivery   INTEGER NOT NULL,
    lead_time_days          INTEGER DEFAULT 1,
    UNIQUE(store_id, product_id)
);

-- ════════════════════════════════════════
-- Purchase orders (PULSE creates, manager approves)
-- ════════════════════════════════════════
CREATE TABLE purchase_orders (
    po_id               VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id          VARCHAR(36) NOT NULL REFERENCES inventory(product_id),
    store_id            VARCHAR(50) NOT NULL REFERENCES stores(store_id),
    supplier_id         VARCHAR(36) REFERENCES suppliers(supplier_id),
    quantity            INTEGER NOT NULL,
    urgency             VARCHAR(10) DEFAULT 'medium'
                        CHECK (urgency IN ('low','medium','high','critical')),
    justification       TEXT,
    revenue_at_risk_aed DECIMAL(10,2),
    status              VARCHAR(20) DEFAULT 'pending'
                        CHECK (status IN ('pending','approved','rejected')),
    manager_note        TEXT,
    created_by          VARCHAR(20) DEFAULT 'PULSE',
    created_at          TIMESTAMP DEFAULT NOW(),
    reviewed_at         TIMESTAMP,
    reviewed_by         VARCHAR(100)
);

CREATE INDEX ON purchase_orders(store_id, status);
CREATE INDEX ON purchase_orders(product_id, status);
```

---

## 2. BigQuery schema (analytics bridge)

```sql
-- Dataset: arc_dataset
-- Region: asia-southeast1 (Singapore)

-- ════════════════════════════════════════
-- Main bridge: ARIA writes, PULSE reads
-- ════════════════════════════════════════
CREATE TABLE IF NOT EXISTS arc_dataset.incidents (
    session_id              STRING NOT NULL,
    customer_id             STRING,
    store_id                STRING,
    timestamp               TIMESTAMP,

    -- What was ordered
    items_ordered           JSON,
    -- [{product_id, product_name, quantity, price_aed}]

    -- What wasn't available
    items_unavailable       JSON,
    -- [{product_id, product_name}]

    -- Substitution outcomes
    substitutions_offered   JSON,
    -- [{original_product_id, substitute_product_id, accepted: bool}]

    -- Promotion
    promotion_id            STRING,
    promotion_saving_aed    FLOAT64,

    -- Cart totals
    cart_total_aed          FLOAT64,
    budget_aed              FLOAT64,

    -- Outcome
    session_sentiment       STRING,   -- positive | neutral | negative
    order_placed            BOOL,
    abandonment_reason      STRING    -- null if order placed
)
PARTITION BY DATE(timestamp)
CLUSTER BY store_id, session_sentiment;

-- ════════════════════════════════════════
-- Inventory change audit log
-- ════════════════════════════════════════
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

-- ════════════════════════════════════════
-- Promotion effectiveness log
-- ════════════════════════════════════════
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

-- ════════════════════════════════════════
-- BigQuery ML demand forecast model
-- (run once after seed data is loaded)
-- ════════════════════════════════════════
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
```

---

## 3. Seed data overview

### Mock MIRA Retail stores (data/seed/customer_profiles.sql)
- 3 stores: Dubai Marina, JBR, Al Barsha
- 5 customer personas: Sarah (halal, family 4), Ahmed (none, single), Fatima (vegetarian, family 3), Kumar (none, couple), Layla (halal, family 5)

### Mock inventory (data/seed/inventory.sql)
- 50 products across 8 categories: dairy, grains, meat (halal), vegetables, fruits, beverages, snacks, cleaning
- Realistic MIRA Retail pricing in AED
- AlloyDB embeddings generated at seed time

### Mock promotions (data/seed/promotions.sql)
- 5 active promotions: rice 10% off, halal chicken bundle, dairy saver pack, fresh veg 15% off, weekend family bundle

### Mock replenishment (data/seed/replenishment.sql)
- Realistic delivery schedules per store per product
- Intentional gap: brown rice at Dubai Marina delivered Tuesday 2PM but peaks Monday-Wednesday 10AM-12PM (the demo scenario)

---

*MIRA Retail · ARC v1.0 · Data Model v1.0*
