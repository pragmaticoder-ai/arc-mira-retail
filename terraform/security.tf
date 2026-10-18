# Random password for database
resource "random_password" "db_password" {
  length  = 24
  special = false
}

# Secret Manager for Database Password
resource "google_secret_manager_secret" "db_password" {
  secret_id = "arc-db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_services]
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Service Account for ARC Backend Services (ARIA, PULSE, Tools)
resource "google_service_account" "backend_sa" {
  account_id   = "arc-backend-sa"
  display_name = "ARC Backend Services Service Account"

  depends_on = [google_project_service.required_services]
}

# IAM Role bindings for Backend Service Account
resource "google_project_iam_member" "backend_bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}
