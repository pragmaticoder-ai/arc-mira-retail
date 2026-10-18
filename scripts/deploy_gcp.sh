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
    echo "Notice: terraform CLI is not installed locally."
    echo "You can install terraform via 'brew install terraform' or deploy Cloud Run services directly using gcloud."
    echo "Deploying Cloud Run services with gcloud..."

    IMAGE_PREFIX="${REGION}-docker.pkg.dev/${PROJECT_ID}/arc-docker-repo"

    # Deploy ARIA Agent
    gcloud run deploy arc-aria-agent \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --image="${IMAGE_PREFIX}/aria-agent:latest" \
        --allow-unauthenticated \
        --min-instances=0 \
        --max-instances=3 \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION},USE_MOCK=true,ENVIRONMENT=production"

    ARIA_URL=$(gcloud run services describe arc-aria-agent --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")

    # Deploy PULSE Agent
    gcloud run deploy arc-pulse-agent \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --image="${IMAGE_PREFIX}/pulse-agent:latest" \
        --allow-unauthenticated \
        --min-instances=0 \
        --max-instances=3 \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION},USE_MOCK=true,ENVIRONMENT=production"

    # Deploy Storefront
    gcloud run deploy arc-storefront \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --image="${IMAGE_PREFIX}/storefront:latest" \
        --allow-unauthenticated \
        --min-instances=0 \
        --max-instances=3 \
        --set-env-vars="ARIA_AGENT_URL=${ARIA_URL},NODE_ENV=production"

    # Deploy PULSE Dashboard
    gcloud run deploy arc-pulse-dashboard \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --image="${IMAGE_PREFIX}/pulse-dashboard:latest" \
        --allow-unauthenticated \
        --min-instances=0 \
        --max-instances=3 \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},USE_MOCK=true"
fi

echo "════════════════════════════════════════════════════════════════════"
echo " Deployment Complete!"
echo "════════════════════════════════════════════════════════════════════"
gcloud run services list --project="${PROJECT_ID}" --region="${REGION}"
