# ════════════════════════════════════════════════════════════════════
# BigQuery Dataset and Tables for ARC Analytics Bridge
# ════════════════════════════════════════════════════════════════════

resource "google_bigquery_dataset" "arc_dataset" {
  dataset_id                  = var.bigquery_dataset_id
  friendly_name               = "ARC Analytics Bridge"
  description                 = "Analytics bridge dataset connecting ARIA shopper sessions to PULSE operational intelligence"
  location                    = var.region
  default_table_expiration_ms = null

  depends_on = [google_project_service.required_services]
}

# ── Main Bridge: incidents table ────────────────────────────────────
resource "google_bigquery_table" "incidents" {
  dataset_id          = google_bigquery_dataset.arc_dataset.dataset_id
  table_id            = "incidents"
  description         = "Customer shopping sessions, unmet demand signals, and feedback"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["store_id", "session_sentiment"]

  schema = jsonencode([
    { name = "session_id", type = "STRING", mode = "REQUIRED" },
    { name = "customer_id", type = "STRING", mode = "NULLABLE" },
    { name = "store_id", type = "STRING", mode = "NULLABLE" },
    { name = "timestamp", type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "items_ordered", type = "JSON", mode = "NULLABLE" },
    { name = "items_unavailable", type = "JSON", mode = "NULLABLE" },
    { name = "demand_signals", type = "JSON", mode = "NULLABLE" },
    { name = "requested_items", type = "JSON", mode = "NULLABLE" },
    { name = "session_status", type = "STRING", mode = "NULLABLE" },
    { name = "substitutions_offered", type = "JSON", mode = "NULLABLE" },
    { name = "promotion_id", type = "STRING", mode = "NULLABLE" },
    { name = "promotion_saving_aed", type = "FLOAT", mode = "NULLABLE" },
    { name = "cart_total_aed", type = "FLOAT", mode = "NULLABLE" },
    { name = "budget_aed", type = "FLOAT", mode = "NULLABLE" },
    { name = "session_sentiment", type = "STRING", mode = "NULLABLE" },
    { name = "order_placed", type = "BOOLEAN", mode = "NULLABLE" },
    { name = "abandonment_reason", type = "STRING", mode = "NULLABLE" }
  ])
}

# ── Inventory Log ───────────────────────────────────────────────────
resource "google_bigquery_table" "inventory_log" {
  dataset_id          = google_bigquery_dataset.arc_dataset.dataset_id
  table_id            = "inventory_log"
  description         = "Audit trail of inventory level changes"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "logged_at"
  }

  clustering = ["store_id", "event_type"]

  schema = jsonencode([
    { name = "log_id", type = "STRING", mode = "REQUIRED" },
    { name = "product_id", type = "STRING", mode = "NULLABLE" },
    { name = "store_id", type = "STRING", mode = "NULLABLE" },
    { name = "event_type", type = "STRING", mode = "NULLABLE" },
    { name = "quantity_before", type = "INTEGER", mode = "NULLABLE" },
    { name = "quantity_after", type = "INTEGER", mode = "NULLABLE" },
    { name = "logged_at", type = "TIMESTAMP", mode = "NULLABLE" }
  ])
}

# ── Promotion Log ───────────────────────────────────────────────────
resource "google_bigquery_table" "promotion_log" {
  dataset_id          = google_bigquery_dataset.arc_dataset.dataset_id
  table_id            = "promotion_log"
  description         = "Promotion application and conversion audit trail"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "logged_at"
  }

  clustering = ["promotion_id"]

  schema = jsonencode([
    { name = "log_id", type = "STRING", mode = "REQUIRED" },
    { name = "promotion_id", type = "STRING", mode = "NULLABLE" },
    { name = "customer_id", type = "STRING", mode = "NULLABLE" },
    { name = "store_id", type = "STRING", mode = "NULLABLE" },
    { name = "cart_before_aed", type = "FLOAT", mode = "NULLABLE" },
    { name = "cart_after_aed", type = "FLOAT", mode = "NULLABLE" },
    { name = "saving_aed", type = "FLOAT", mode = "NULLABLE" },
    { name = "converted", type = "BOOLEAN", mode = "NULLABLE" },
    { name = "logged_at", type = "TIMESTAMP", mode = "NULLABLE" }
  ])
}
