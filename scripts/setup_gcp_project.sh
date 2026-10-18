#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════
# Google Cloud Project Setup & API Initialization Script
# ════════════════════════════════════════════════════════════════════
set -euo pipefail

PROJECT_ID="${1:-aria-mira-retail}"
REGION="${2:-asia-southeast1}"
BILLING_ACCOUNT_ID="${3:-016030-32803C-4259E4}"

echo "════════════════════════════════════════════════════════════════════"
echo " Setting up Google Cloud for ARC Project: ${PROJECT_ID}"
echo " Region: ${REGION}"
echo "════════════════════════════════════════════════════════════════════"

# 1. Set active project in gcloud
echo "--> Configuring active gcloud project..."
gcloud config set project "${PROJECT_ID}"

# 2. Check billing status
echo "--> Checking billing account status..."
BILLING_ENABLED=$(gcloud billing projects describe "${PROJECT_ID}" --format="value(billingEnabled)" 2>/dev/null || echo "false")

if [ "${BILLING_ENABLED}" != "true" ]; then
    echo "--> Billing is currently NOT enabled for ${PROJECT_ID}."
    if [ -n "${BILLING_ACCOUNT_ID}" ]; then
        echo "--> Linking project to Billing Account: ${BILLING_ACCOUNT_ID}..."
        gcloud billing projects link "${PROJECT_ID}" --billing-account="${BILLING_ACCOUNT_ID}"
        echo "--> Billing successfully linked!"
    else
        echo "--> WARNING: Please link a billing account to continue: gcloud billing projects link ${PROJECT_ID} --billing-account=<ACCOUNT_ID>"
        exit 1
    fi
else
    echo "--> Billing is already enabled for ${PROJECT_ID}."
fi

# 3. Enable essential Google Cloud Services
echo "--> Enabling required Google Cloud APIs..."
SERVICES=(
    "compute.googleapis.com"
    "run.googleapis.com"
    "artifactregistry.googleapis.com"
    "cloudbuild.googleapis.com"
    "secretmanager.googleapis.com"
    "bigquery.googleapis.com"
    "bigquerystorage.googleapis.com"
    "aiplatform.googleapis.com"
    "alloydb.googleapis.com"
    "sqladmin.googleapis.com"
    "servicenetworking.googleapis.com"
    "vpcaccess.googleapis.com"
    "iam.googleapis.com"
    "logging.googleapis.com"
    "monitoring.googleapis.com"
)

gcloud services enable "${SERVICES[@]}" --project="${PROJECT_ID}"

echo "--> All required APIs enabled successfully!"
echo "════════════════════════════════════════════════════════════════════"
echo " Setup complete! You are ready to run Terraform or deploy_gcp.sh."
echo "════════════════════════════════════════════════════════════════════"
