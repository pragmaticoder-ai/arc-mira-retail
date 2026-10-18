variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
  default     = "aria-mira-retail"
}

variable "region" {
  description = "The Google Cloud region for regional resources"
  type        = string
  default     = "asia-southeast1"
}

variable "zone" {
  description = "The Google Cloud zone for zonal resources"
  type        = string
  default     = "asia-southeast1-a"
}

variable "environment" {
  description = "Environment name (e.g. hackathon, staging, production)"
  type        = string
  default     = "hackathon"
}

variable "enable_alloydb" {
  description = "Whether to provision an AlloyDB cluster. Set to false during development/hackathons to avoid high minimum cluster costs ($150+/mo), and use Cloud SQL instead."
  type        = bool
  default     = false
}

variable "use_cloud_sql" {
  description = "Whether to provision Cloud SQL PostgreSQL when enable_alloydb is false"
  type        = bool
  default     = true
}

variable "cloud_sql_tier" {
  description = "The machine type for Cloud SQL PostgreSQL (e.g. db-f1-micro for lowest cost hackathon testing, db-custom-1-3840 for standard)"
  type        = string
  default     = "db-f1-micro"
}

variable "alloydb_cluster_id" {
  description = "AlloyDB cluster ID if enable_alloydb is true"
  type        = string
  default     = "arc-alloydb-cluster"
}

variable "db_name" {
  description = "Database name for ARC operational state"
  type        = string
  default     = "postgres"
}

variable "db_user" {
  description = "Database user for ARC services"
  type        = string
  default     = "arc_admin"
}

variable "bigquery_dataset_id" {
  description = "BigQuery dataset ID for incident analytics bridge"
  type        = string
  default     = "arc_dataset"
}

variable "cloud_run_min_instances" {
  description = "Minimum instances for Cloud Run services (0 = scale to zero when idle, saving cost)"
  type        = number
  default     = 0
}

variable "cloud_run_max_instances" {
  description = "Maximum instances for Cloud Run services"
  type        = number
  default     = 3
}

variable "deploy_cloud_run_services" {
  description = "Whether to declare Cloud Run services in Terraform (requires container images to exist in Artifact Registry or placeholder image)"
  type        = bool
  default     = true
}

variable "use_mock" {
  description = "Default USE_MOCK flag for Cloud Run services. Set to true for initial deployment before wiring live AlloyDB credentials."
  type        = bool
  default     = true
}
