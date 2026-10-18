-- ════════════════════════════════════════════════════════════════════
-- ARC — AlloyDB schema (operational data)
-- Source of truth: DATA_MODEL.md §1
-- Compatible with Cloud SQL PostgreSQL and AlloyDB with pgvector enabled.
-- ════════════════════════════════════════════════════════════════════

-- ── Extensions ──────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;
-- Gemini embeddings are generated through the Google Gen AI SDK.

-- ── Stores ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stores (
    store_id        VARCHAR(50) PRIMARY KEY,
    store_name      VARCHAR(200) NOT NULL,
    area            VARCHAR(100),
    city            VARCHAR(50) DEFAULT 'Dubai',
    address         TEXT,
    is_active       BOOLEAN DEFAULT true
);

-- ── Customer profiles ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customer_profiles (
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

-- ── Suppliers ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id     VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_name   VARCHAR(200) NOT NULL,
    contact_email   VARCHAR(100),
    lead_time_days  INTEGER DEFAULT 2
);

-- ── Inventory (with Google text embeddings) ───────────────────
CREATE TABLE IF NOT EXISTS inventory (
    product_id          VARCHAR(36) NOT NULL,
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
    -- Perishable discount support (ARIA surfacing + PULSE discount tool)
    is_perishable       BOOLEAN DEFAULT false,
    expiry_date         DATE,
    discount_active     BOOLEAN DEFAULT false,
    discount_pct        DECIMAL(5,2),
    embedding           vector(768),    -- Google embeddings; exact cosine search
    updated_at          TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (product_id, store_id)
);

-- Exact pgvector search is sufficient for this catalog; no ScaNN dependency.
CREATE INDEX IF NOT EXISTS idx_inventory_store_id_category ON inventory(store_id, category);
CREATE INDEX IF NOT EXISTS idx_inventory_store_id_stock_quantity ON inventory(store_id, stock_quantity);

-- ── Orders ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
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

CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_store_id_created_at ON orders(store_id, created_at);

-- ── Promotions ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS promotions (
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

-- ── Replenishment schedules ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS replenishment_schedule (
    schedule_id             VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id                VARCHAR(50) NOT NULL REFERENCES stores(store_id),
    product_id              VARCHAR(36) NOT NULL,
    supplier_id             VARCHAR(36) REFERENCES suppliers(supplier_id),
    delivery_day            VARCHAR(20),    -- Monday, Tuesday...
    delivery_time           TIME,
    quantity_per_delivery   INTEGER NOT NULL,
    lead_time_days          INTEGER DEFAULT 1,
    UNIQUE(store_id, product_id)
);

-- ── Purchase orders (PULSE creates, manager approves) ───────────────
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id               VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id          VARCHAR(36) NOT NULL,
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

CREATE INDEX IF NOT EXISTS idx_purchase_orders_store_id_status ON purchase_orders(store_id, status);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_product_id_status ON purchase_orders(product_id, status);

-- Runtime documents: one record per session, order, PO, or manager decision.
-- Inventory and customer profiles above remain authoritative SQL tables.
CREATE TABLE IF NOT EXISTS arc_records (
    entity TEXT NOT NULL CHECK (entity IN ('sessions','orders','purchase_orders','decisions')),
    key TEXT NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (entity, key)
);
