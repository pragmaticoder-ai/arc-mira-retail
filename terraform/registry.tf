# Artifact Registry Docker repository for ARC container images
resource "google_artifact_registry_repository" "arc_repo" {
  location      = var.region
  repository_id = "arc-docker-repo"
  description   = "Docker container images for ARC (Storefront, ARIA, PULSE, Tools)"
  format        = "DOCKER"

  depends_on = [google_project_service.required_services]
}
