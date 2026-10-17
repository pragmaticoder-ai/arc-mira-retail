# DEPLOYMENT.md — Google Cloud Setup & Deploy Guide
> MIRA Retail · ARC v1.0

---

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated
- Python 3.11+
- Docker (for local testing)

---

## 1. Google Cloud project setup

```bash
# Create project
gcloud projects create mira-arc-hackathon --name="MIRA Retail ARC"
gcloud config set project mira-arc-hackathon

# Enable billing (required for AlloyDB)
# Do this in the Cloud Console: https://console.cloud.google.com/billing

# Enable all required APIs
gcloud services enable \
    aiplatform.googleapis.com \
    alloydb.googleapis.com \
    bigquery.googleapis.com \
    bigquerymigration.googleapis.com \
    bigqueryml.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    cloudfunctions.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    vpcaccess.googleapis.com \
    servicenetworking.googleapis.com \
    cloudresourcemanager.googleapis.com

# Set region
gcloud config set run/region asia-southeast1
gcloud config set compute/region asia-southeast1
```

---

## 2. IAM service accounts

```bash
# Create service account for agents
gcloud iam service-accounts create arc-agent-sa \
    --display-name="ARC Agent Service Account"

# Create service account for tool functions
gcloud iam service-accounts create arc-tools-sa \
    --display-name="ARC Tool Functions Service Account"

# Grant roles to agent SA
gcloud projects add-iam-policy-binding mira-arc-hackathon \
    --member="serviceAccount:arc-agent-sa@mira-arc-hackathon.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding mira-arc-hackathon \
    --member="serviceAccount:arc-agent-sa@mira-arc-hackathon.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

# Grant roles to tools SA
gcloud projects add-iam-policy-binding mira-arc-hackathon \
    --member="serviceAccount:arc-tools-sa@mira-arc-hackathon.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding mira-arc-hackathon \
    --member="serviceAccount:arc-tools-sa@mira-arc-hackathon.iam.gserviceaccount.com" \
    --role="roles/alloydb.client"

gcloud projects add-iam-policy-binding mira-arc-hackathon \
    --member="serviceAccount:arc-tools-sa@mira-arc-hackathon.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

## 3. Secret Manager

```bash
# Store AlloyDB password
echo -n "your-alloydb-password" | \
    gcloud secrets create alloydb-password --data-file=-

# Store AlloyDB connection details
echo -n "your-alloydb-host-ip" | \
    gcloud secrets create alloydb-host --data-file=-
```

---

## 4. AlloyDB setup

```bash
# Create VPC network for AlloyDB (private IP)
gcloud compute networks create arc-vpc --subnet-mode=auto

# Create AlloyDB cluster
gcloud alloydb clusters create arc-alloydb-cluster \
    --region=asia-southeast1 \
    --password=$(gcloud secrets versions access latest --secret=alloydb-password) \
    --network=arc-vpc

# Create primary instance
gcloud alloydb instances create arc-alloydb-primary \
    --instance-type=PRIMARY \
    --cpu-count=2 \
    --region=asia-southeast1 \
    --cluster=arc-alloydb-cluster

# Get the AlloyDB IP
gcloud alloydb instances describe arc-alloydb-primary \
    --cluster=arc-alloydb-cluster \
    --region=asia-southeast1 \
    --format="value(ipAddress)"

# Connect and run schema
# (from Cloud Shell or a VM in the same VPC)
psql "host=<ALLOYDB_IP> user=postgres dbname=postgres" \
    -f data/schema/alloydb_schema.sql

# Seed mock data
psql "host=<ALLOYDB_IP> user=postgres dbname=postgres" \
    -f data/seed/customer_profiles.sql \
    -f data/seed/inventory.sql \
    -f data/seed/promotions.sql \
    -f data/seed/replenishment.sql

# Generate AlloyDB AI embeddings
psql "host=<ALLOYDB_IP> user=postgres dbname=postgres" -c "
UPDATE inventory
SET embedding = embedding('textembedding-gecko@003',
    product_name || ' ' || COALESCE(category,'') || ' ' || COALESCE(dietary_flags,''))
WHERE embedding IS NULL;"
```

---

## 5. BigQuery setup

```bash
# Create dataset
bq mk --dataset \
    --location=asia-southeast1 \
    --description="ARC analytics bridge for MIRA Retail" \
    mira-arc-hackathon:arc_dataset

# Create tables
bq query --use_legacy_sql=false < data/schema/bigquery_schema.sql

# Train BigQuery ML model (after seed data is loaded)
bq query --use_legacy_sql=false "
CREATE OR REPLACE MODEL arc_dataset.demand_forecast
OPTIONS(model_type='ARIMA_PLUS', ...) AS ..."
```

---

## 6. Artifact Registry

```bash
# Create Docker repository
gcloud artifacts repositories create arc-registry \
    --repository-format=docker \
    --location=asia-southeast1 \
    --description="ARC container images"

# Authenticate Docker
gcloud auth configure-docker asia-southeast1-docker.pkg.dev
```

---

## 7. Deploy tool functions

```bash
# Build and push tool functions image
cd tools/
docker build -t asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-tools:latest .
docker push asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-tools:latest

# Deploy ARIA tools as Cloud Run service
gcloud run deploy arc-aria-tools \
    --image=asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-tools:latest \
    --region=asia-southeast1 \
    --service-account=arc-tools-sa@mira-arc-hackathon.iam.gserviceaccount.com \
    --no-allow-unauthenticated \
    --set-env-vars="AGENT_TYPE=aria"

# Deploy PULSE tools as Cloud Run service
gcloud run deploy arc-pulse-tools \
    --image=asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-tools:latest \
    --region=asia-southeast1 \
    --service-account=arc-tools-sa@mira-arc-hackathon.iam.gserviceaccount.com \
    --no-allow-unauthenticated \
    --set-env-vars="AGENT_TYPE=pulse"
```

---

## 8. Deploy agents

```bash
# Deploy ARIA agent
cd agents/aria/
gcloud run deploy arc-aria-agent \
    --image=asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-aria:latest \
    --region=asia-southeast1 \
    --service-account=arc-agent-sa@mira-arc-hackathon.iam.gserviceaccount.com \
    --no-allow-unauthenticated

# Deploy PULSE agent
cd agents/pulse/
gcloud run deploy arc-pulse-agent \
    --image=asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-pulse:latest \
    --region=asia-southeast1 \
    --service-account=arc-agent-sa@mira-arc-hackathon.iam.gserviceaccount.com \
    --no-allow-unauthenticated
```

---

## 9. Deploy frontends

### ARIA customer app (Next.js)
```bash
cd frontend/aria-app/

# Build Next.js Docker image
docker build -t asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-aria-app:latest .
docker push asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-aria-app:latest

# Deploy to Cloud Run
gcloud run deploy arc-aria-app \
    --image=asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-aria-app:latest \
    --region=asia-southeast1 \
    --allow-unauthenticated \
    --set-env-vars="ARIA_AGENT_URL=https://arc-aria-agent-xxxx-as.a.run.app"
```

### PULSE manager dashboard (Streamlit)
```bash
cd frontend/pulse-dashboard/

docker build -t asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-pulse-dashboard:latest .
docker push asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-pulse-dashboard:latest

gcloud run deploy arc-pulse-dashboard \
    --image=asia-southeast1-docker.pkg.dev/mira-arc-hackathon/arc-registry/arc-pulse-dashboard:latest \
    --region=asia-southeast1 \
    --allow-unauthenticated \
    --set-env-vars="PULSE_AGENT_URL=https://arc-pulse-agent-xxxx-as.a.run.app"
```

---

## 10. Local development

```bash
# Run ARIA agent locally with ADK dev server
cd agents/aria
adk web .
# Opens http://localhost:8000

# Run PULSE agent locally
cd agents/pulse
adk web .
# Opens http://localhost:8001

# Run Streamlit frontends locally
streamlit run frontend/aria_chat.py --server.port 8501
streamlit run frontend/pulse_dashboard.py --server.port 8502
```

---

## 11. Environment variables reference

```env
# Google Cloud
GOOGLE_CLOUD_PROJECT=mira-arc-hackathon
GOOGLE_CLOUD_REGION=asia-southeast1

# AlloyDB (fetched from Secret Manager in production)
ALLOYDB_HOST=<private-ip>
ALLOYDB_PORT=5432
ALLOYDB_DATABASE=postgres
ALLOYDB_USER=postgres

# BigQuery
BIGQUERY_DATASET=arc_dataset
BIGQUERY_LOCATION=asia-southeast1

# Vertex AI
VERTEX_AI_LOCATION=asia-southeast1
GEMINI_PRO_MODEL=gemini-1.5-pro
GEMINI_FLASH_MODEL=gemini-1.5-flash-001

# Cloud Run service URLs (set after deploy)
ARIA_TOOLS_URL=https://arc-aria-tools-xxxx-as.a.run.app
PULSE_TOOLS_URL=https://arc-pulse-tools-xxxx-as.a.run.app
```

---

*MIRA Retail · ARC v1.0 · Deployment v1.0*
