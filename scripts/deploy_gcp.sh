#!/usr/bin/env bash
# Deploy against the existing Cloud SQL/BigQuery resources in Singapore.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ID="${1:-aria-mira-retail}"
REGION="${2:-asia-southeast1}"
if [[ "${3:-}" == "--local-only" ]]; then
  exec "${ROOT_DIR}/.venv/bin/python" "${SCRIPT_DIR}/provision_local_gcp.py" --project "${PROJECT_ID}" --region "${REGION}"
fi
TAG="${3:-$(git -C "${ROOT_DIR}" rev-parse --short HEAD)}"
exec "${ROOT_DIR}/.venv/bin/python" -u "${SCRIPT_DIR}/deploy_cloud_run.py" --project "${PROJECT_ID}" --region "${REGION}" --tag "${TAG}" --wait-build
