# Google Cloud APIs required for ARC (Agentic Retail Command)
locals {
  services = [
    "compute.googleapis.com",              # VPC networking
    "run.googleapis.com",                  # Cloud Run
    "artifactregistry.googleapis.com",      # Container registry
    "cloudbuild.googleapis.com",            # CI/CD builds
    "secretmanager.googleapis.com",        # Secret management
    "bigquery.googleapis.com",             # BigQuery analytics bridge & ML
    "bigquerystorage.googleapis.com",      # BigQuery storage API
    "aiplatform.googleapis.com",           # Vertex AI Gemini & Embeddings
    "alloydb.googleapis.com",              # AlloyDB for PostgreSQL
    "sqladmin.googleapis.com",             # Cloud SQL Admin API
    "servicenetworking.googleapis.com",     # Private services networking
    "vpcaccess.googleapis.com",            # Serverless VPC Access connector
    "iam.googleapis.com",                  # Cloud IAM
    "logging.googleapis.com",              # Cloud Logging
    "monitoring.googleapis.com",           # Cloud Monitoring
  ]
}

resource "google_project_service" "required_services" {
  for_each = toset(locals.services)

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}
