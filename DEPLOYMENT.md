# Deploy and run ARC

Updated October 18, 2026.

ARIA and PULSE run on Google Cloud Run in `aria-mira-retail`, region
`asia-southeast1`, using the existing Cloud SQL catalog, BigQuery events and
Vertex AI/Gemini models. See the [Cloud Run runbook](docs/CLOUD_RUN.md) for
access, configuration, deployment and end-to-end tests.

| Application | URL |
|---|---|
| ARIA shopping app | https://arc-storefront-kif65kxodq-as.a.run.app |
| PULSE manager app | https://arc-pulse-dashboard-kif65kxodq-as.a.run.app |

The agent services are private. The storefront uses its service-account identity
to call ARIA; the dashboard uses its identity to request PULSE's Google summary.
Browser apps have separate demo credentials, stored in Secret Manager and in the
gitignored local file `data/local/cloud/ACCESS.md`. Database/service-account
credentials are not shopper login credentials.

## Cloud deployment

```sh
bash scripts/deploy_gcp.sh aria-mira-retail asia-southeast1
```

This builds the four containers with Cloud Build, publishes them to Artifact
Registry, and deploys the services with runtime identities and managed secrets.
It reuses Cloud SQL instance `arc-postgres-instance`, database `arc`, and
BigQuery dataset `arc_dataset`. It does not apply Terraform, recreate data stores,
or replace the enriched catalog with mock data.

Supply a unique image tag as the third argument to label a release:

```sh
bash scripts/deploy_gcp.sh aria-mira-retail asia-southeast1 demo-20261018
```

The deployment writes its manifest to `data/local/cloud/deployment.json`.
[docs/CLOUD_RUN.md](docs/CLOUD_RUN.md) explains staged builds, service limits,
credentials, shopper tests, and the manager feedback loop.

## Run locally against Google

Prerequisites: Python 3.11+, uv, Node/npm, Google Cloud CLI and Application
Default Credentials with the configured project permissions.

```sh
uv sync --group dev
npm --prefix frontend/aria-app ci
.venv/bin/python scripts/check_google.py
.venv/bin/python scripts/run_local.py --skip-checks
```

| Local surface | URL |
|---|---|
| ARIA storefront | http://localhost:3000 |
| ARIA API | http://127.0.0.1:8001 |
| PULSE API | http://127.0.0.1:8002 |
| PULSE dashboard | http://localhost:8501 |

See [LOCAL_GOOGLE.md](docs/LOCAL_GOOGLE.md) for environment values and Google
provisioning. The Python SQL connector supplies encrypted Cloud SQL connections;
a local proxy and browser installation are not required.

Explicit offline fixtures remain available with
`.venv/bin/python scripts/run_local.py --offline`. SQLite state and bridge paths
must differ. Do not use offline mode to validate the hosted Google adapters.

## Verification

```sh
.venv/bin/pytest -q
npm --prefix frontend/aria-app run build
.venv/bin/python scripts/smoke_cloud.py
```

The cloud smoke test requires a completed local deployment manifest and access
file. It checks protected pages/APIs, catalog pagination, seafood filtering,
weekly basket availability, checkout/order history and the PULSE Google summary.
It removes its own temporary shopper records and restores stock used by its
single demo order. It does not approve manager actions.

Payments, supplier delivery and logistics execution remain outside this
hackathon prototype. A saved demo order reserves inventory and persists its
record; it does not take payment or dispatch a shipment.
