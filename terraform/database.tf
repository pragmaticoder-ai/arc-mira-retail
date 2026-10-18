# ════════════════════════════════════════════════════════════════════
# Database Configuration: Cloud SQL (Default) or AlloyDB
# ════════════════════════════════════════════════════════════════════

# ── Cloud SQL PostgreSQL (Cost-Optimized Option for Hackathons) ───────
resource "google_sql_database_instance" "postgres" {
  count            = (!var.enable_alloydb && var.use_cloud_sql) ? 1 : 0
  name             = "arc-postgres-instance"
  database_version = "POSTGRES_15"
  region           = var.region

  depends_on = [
    google_service_networking_connection.private_vpc_connection,
    google_project_service.required_services
  ]

  settings {
    tier              = var.cloud_sql_tier
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.arc_vpc.id
      enable_private_path_for_google_cloud_services = true
    }

    backup_configuration {
      enabled = false # Disabled for hackathon cost/simplicity
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "arc_db" {
  count    = (!var.enable_alloydb && var.use_cloud_sql) ? 1 : 0
  name     = var.db_name
  instance = google_sql_database_instance.postgres[0].name
}

resource "google_sql_user" "arc_user" {
  count    = (!var.enable_alloydb && var.use_cloud_sql) ? 1 : 0
  name     = var.db_user
  instance = google_sql_database_instance.postgres[0].name
  password = random_password.db_password.result
}

# ── AlloyDB for PostgreSQL (High-Performance Vector Option) ───────────
resource "google_alloydb_cluster" "arc_cluster" {
  count      = var.enable_alloydb ? 1 : 0
  cluster_id = var.alloydb_cluster_id
  location   = var.region

  network_config {
    network = google_compute_network.arc_vpc.id
  }

  initial_user {
    user     = var.db_user
    password = random_password.db_password.result
  }

  depends_on = [
    google_service_networking_connection.private_vpc_connection,
    google_project_service.required_services
  ]
}

resource "google_alloydb_instance" "arc_primary" {
  count         = var.enable_alloydb ? 1 : 0
  cluster       = google_alloydb_cluster.arc_cluster[0].name
  instance_id   = "${var.alloydb_cluster_id}-primary"
  instance_type = "PRIMARY"

  machine_config {
    cpu_count = 2
  }

  depends_on = [google_alloydb_cluster.arc_cluster]
}

# Locals to resolve active database host
locals {
  db_host = var.enable_alloydb ? (
    length(google_alloydb_instance.arc_primary) > 0 ? google_alloydb_instance.arc_primary[0].ip_address : ""
  ) : (
    length(google_sql_database_instance.postgres) > 0 ? google_sql_database_instance.postgres[0].private_ip_address : ""
  )
}
