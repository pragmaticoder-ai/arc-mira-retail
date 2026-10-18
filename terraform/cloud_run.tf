# ════════════════════════════════════════════════════════════════════
# Cloud Run Services for ARC (Agentic Retail Command)
# ════════════════════════════════════════════════════════════════════

locals {
  image_prefix = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.arc_repo.repository_id}"
}

# ── 1. ARIA Agent Service ───────────────────────────────────────────
resource "google_cloud_run_v2_service" "aria_agent" {
  count    = var.deploy_cloud_run_services ? 1 : 0
  name     = "arc-aria-agent"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend_sa.email

    scaling {
      min_instance_count = var.cloud_run_min_instances
      max_instance_count = var.cloud_run_max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.arc_connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${local.image_prefix}/aria-agent:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_REGION"
        value = var.region
      }
      env {
        name  = "VERTEX_AI_LOCATION"
        value = var.region
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = var.bigquery_dataset_id
      }
      env {
        name  = "ALLOYDB_HOST"
        value = local.db_host
      }
      env {
        name  = "ALLOYDB_PORT"
        value = "5432"
      }
      env {
        name  = "ALLOYDB_DATABASE"
        value = var.db_name
      }
      env {
        name  = "ALLOYDB_USER"
        value = var.db_user
      }
      env {
        name = "ALLOYDB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "USE_MOCK"
        value = var.use_mock ? "true" : "false"
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
    }
  }

  depends_on = [
    google_project_service.required_services,
    google_vpc_access_connector.arc_connector
  ]
}

# ── 2. PULSE Agent Service ──────────────────────────────────────────
resource "google_cloud_run_v2_service" "pulse_agent" {
  count    = var.deploy_cloud_run_services ? 1 : 0
  name     = "arc-pulse-agent"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend_sa.email

    scaling {
      min_instance_count = var.cloud_run_min_instances
      max_instance_count = var.cloud_run_max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.arc_connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${local.image_prefix}/pulse-agent:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_REGION"
        value = var.region
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = var.bigquery_dataset_id
      }
      env {
        name  = "ALLOYDB_HOST"
        value = local.db_host
      }
      env {
        name  = "ALLOYDB_PORT"
        value = "5432"
      }
      env {
        name  = "ALLOYDB_DATABASE"
        value = var.db_name
      }
      env {
        name  = "ALLOYDB_USER"
        value = var.db_user
      }
      env {
        name = "ALLOYDB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "USE_MOCK"
        value = var.use_mock ? "true" : "false"
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
    }
  }

  depends_on = [
    google_project_service.required_services,
    google_vpc_access_connector.arc_connector
  ]
}

# ── 3. ARIA Storefront (Next.js Frontend) ────────────────────────────
resource "google_cloud_run_v2_service" "storefront" {
  count    = var.deploy_cloud_run_services ? 1 : 0
  name     = "arc-storefront"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = var.cloud_run_min_instances
      max_instance_count = var.cloud_run_max_instances
    }

    containers {
      image = "${local.image_prefix}/storefront:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "ARIA_AGENT_URL"
        value = length(google_cloud_run_v2_service.aria_agent) > 0 ? google_cloud_run_v2_service.aria_agent[0].uri : "http://localhost:8001"
      }
      env {
        name  = "NODE_ENV"
        value = "production"
      }
    }
  }

  depends_on = [
    google_project_service.required_services,
    google_cloud_run_v2_service.aria_agent
  ]
}

# ── 4. PULSE Manager Dashboard (Streamlit Frontend) ──────────────────
resource "google_cloud_run_v2_service" "pulse_dashboard" {
  count    = var.deploy_cloud_run_services ? 1 : 0
  name     = "arc-pulse-dashboard"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend_sa.email

    scaling {
      min_instance_count = var.cloud_run_min_instances
      max_instance_count = var.cloud_run_max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.arc_connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${local.image_prefix}/pulse-dashboard:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = var.bigquery_dataset_id
      }
      env {
        name  = "ALLOYDB_HOST"
        value = local.db_host
      }
      env {
        name  = "ALLOYDB_PORT"
        value = "5432"
      }
      env {
        name  = "ALLOYDB_DATABASE"
        value = var.db_name
      }
      env {
        name  = "ALLOYDB_USER"
        value = var.db_user
      }
      env {
        name = "ALLOYDB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "USE_MOCK"
        value = var.use_mock ? "true" : "false"
      }
    }
  }

  depends_on = [
    google_project_service.required_services,
    google_vpc_access_connector.arc_connector
  ]
}

# ── Allow Unauthenticated Public Access for Demo ─────────────────────
resource "google_cloud_run_service_iam_member" "storefront_public" {
  count    = var.deploy_cloud_run_services ? 1 : 0
  location = var.region
  service  = google_cloud_run_v2_service.storefront[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "pulse_dashboard_public" {
  count    = var.deploy_cloud_run_services ? 1 : 0
  location = var.region
  service  = google_cloud_run_v2_service.pulse_dashboard[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "aria_agent_public" {
  count    = var.deploy_cloud_run_services ? 1 : 0
  location = var.region
  service  = google_cloud_run_v2_service.aria_agent[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "pulse_agent_public" {
  count    = var.deploy_cloud_run_services ? 1 : 0
  location = var.region
  service  = google_cloud_run_v2_service.pulse_agent[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
