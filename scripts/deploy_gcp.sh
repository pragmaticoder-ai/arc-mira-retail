#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════
# Master Deployment Script for ARC on Google Cloud
# ════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

PROJECT_ID="${1:-aria-mira-retail}"
REGION="${2:-asia-southeast1}"

echo "════════════════════════════════════════════════════════════════════"
echo " Deploying ARC to Google Cloud"
echo " Project: ${PROJECT_ID} | Region: ${REGION}"
echo "════════════════════════════════════════════════════════════════════"

# Local execution needs cloud dependencies, not published app containers.
if [[ "${3:-}" == "--local-only" ]]; then
    exec "${ROOT_DIR}/.venv/bin/python" "${SCRIPT_DIR}/provision_local_gcp.py" --project "${PROJECT_ID}" --region "${REGION}"
fi

if ! command -v terraform &> /dev/null; then
    echo "Terraform is required for Cloud Run deployment; use --local-only for local apps." >&2
    exit 1
fi

# 1. Project Setup & API Enablement
echo "Step 1: Setting up project and enabling APIs..."
bash "${SCRIPT_DIR}/setup_gcp_project.sh" "${PROJECT_ID}" "${REGION}"

# 2. Ensure Artifact Registry repository exists
echo "Step 2: Ensuring Artifact Registry repository exists..."
gcloud artifacts repositories create arc-docker-repo \
    --repository-format=docker \
    --location="${REGION}" \
    --description="ARC Docker Repository" \
    --project="${PROJECT_ID}" 2>/dev/null || echo "--> Repository arc-docker-repo already exists or created."

# 3. Build and Push Container Images with Cloud Build
echo "Step 3: Building and pushing containers via Google Cloud Build..."
gcloud builds submit "${ROOT_DIR}" \
    --project="${PROJECT_ID}" \
    --config="${ROOT_DIR}/cloudbuild.yaml" \
    --substitutions="_REGION=${REGION}"

# 3. Provision Infrastructure with Terraform
echo "Step 3: Provisioning Google Cloud Infrastructure via Terraform..."
cd "${ROOT_DIR}/terraform"

if [ ! -f "terraform.tfvars" ] && [ -f "terraform.tfvars.example" ]; then
    echo "Creating terraform.tfvars from example..."
    cp terraform.tfvars.example terraform.tfvars
fi

if command -v terraform &> /dev/null; then
    terraform init
    terraform apply -auto-approve \
        -var="project_id=${PROJECT_ID}" \
        -var="region=${REGION}"
else
    echo "Terraform is required for Cloud Run deployment. Use --local-only to provision dependencies for local apps." >&2
    exit 1
fi

echo "════════════════════════════════════════════════════════════════════"
echo " Deployment Complete!"
echo "════════════════════════════════════════════════════════════════════"
gcloud run services list --project="${PROJECT_ID}" --region="${REGION}"
