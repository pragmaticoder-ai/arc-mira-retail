output "project_id" {
  description = "The Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud region"
  value       = var.region
}

output "artifact_registry_repo" {
  description = "Artifact Registry Docker repository"
  value       = google_artifact_registry_repository.arc_repo.id
}

output "bigquery_dataset" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.arc_dataset.dataset_id
}

output "database_host" {
  description = "Internal IP address of the operational database"
  value       = local.db_host
}

output "database_user" {
  description = "Database username"
  value       = var.db_user
}

output "storefront_url" {
  description = "Public URL for ARIA Next.js Storefront"
  value       = length(google_cloud_run_v2_service.storefront) > 0 ? google_cloud_run_v2_service.storefront[0].uri : null
}

output "pulse_dashboard_url" {
  description = "Public URL for PULSE Streamlit Dashboard"
  value       = length(google_cloud_run_v2_service.pulse_dashboard) > 0 ? google_cloud_run_v2_service.pulse_dashboard[0].uri : null
}

output "aria_agent_url" {
  description = "Public URL for ARIA Agent Backend"
  value       = length(google_cloud_run_v2_service.aria_agent) > 0 ? google_cloud_run_v2_service.aria_agent[0].uri : null
}

output "pulse_agent_url" {
  description = "Public URL for PULSE Agent Backend"
  value       = length(google_cloud_run_v2_service.pulse_agent) > 0 ? google_cloud_run_v2_service.pulse_agent[0].uri : null
}
