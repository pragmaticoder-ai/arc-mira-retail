# Hosted ARIA and PULSE

The Cloud Run deployment reuses project `aria-mira-retail`, region
`asia-southeast1`, Cloud SQL instance `arc-postgres-instance`, database `arc`,
and BigQuery dataset `arc_dataset`. It does not recreate the database, import
mock data, or overwrite the enriched MIRA catalog.

## Deploy

```sh
# Requires gcloud login and the project's deploy/IAM permissions.
bash scripts/deploy_gcp.sh aria-mira-retail asia-southeast1
```

The script builds four containers with Cloud Build, pushes them to Artifact
Registry, and deploys the following services. It does not run Terraform against
the existing resources.

| Cloud Run service | Purpose | Access |
|---|---|---|
| arc-storefront | ARIA shopping application | HTTPS, browser demo username/password |
| arc-pulse-dashboard | PULSE manager dashboard | HTTPS, manager sign-in form |
| arc-aria-agent | Shopping/checkout API | Private; storefront service identity |
| arc-pulse-agent | Operations/Gemini API | Private; dashboard service identity |

Runtime service accounts use Google-managed credentials. Backends obtain the
existing database password through a Secret Manager environment injection.
The storefront calls ARIA with a renewable audience-specific identity token;
PULSE's dashboard does the same when requesting a Gemini operations summary.

Containers scale to zero, with a maximum of two instances per service. The
initial visit can take longer while a container starts. These limits do not
remove existing database charges.

Build independently, then deploy a successfully published tag:

```sh
.venv/bin/python scripts/deploy_cloud_run.py --tag=demo-20261018
# Inspect the printed Cloud Build ID until it succeeds, then:
.venv/bin/python scripts/deploy_cloud_run.py --tag=demo-20261018 --skip-build
```

Use a new tag after source changes. Deployment code changes must be committed
alongside application changes to make a particular release reproducible.

## URLs and access

- ARIA: https://arc-storefront-kif65kxodq-as.a.run.app
- PULSE: https://arc-pulse-dashboard-kif65kxodq-as.a.run.app


The completed deployment writes URLs to `data/local/cloud/deployment.json`
and demo credentials to `data/local/cloud/ACCESS.md`. Both are gitignored;
passwords also live in Secret Manager. The access file has owner-only permissions.

ARIA uses a browser username/password prompt. PULSE uses its manager form.
The accounts protect a shared fictional demo, not production customer accounts
or enterprise SSO. Do not use your Google account or database password there.

To list deployed addresses:

```sh
gcloud run services list --project=aria-mira-retail --region=asia-southeast1
```

## Test the shopper journey

1. Open the ARIA storefront URL and enter its demo credentials.
2. Search for a product, open its details and add it to the basket. Check images,
   pack sizes and AED prices. Try a brand facet and a second listing page.
3. Ask: `Weekly halal groceries, family of 4, AED 300. Include brown rice.`
   Check the household and total at or below AED 300. The current brown-rice
   SKU is out of stock: ARIA must disclose that and offer an alternative without
   silently adding it or claiming brown rice is in the basket.
   Non-meat groceries and seafood do not require a halal slaughter label.
4. Open the cart icon. Change quantities or remove an item, then review the
   updated quote. Explicitly confirm only if you want to save a demo order.
5. Open **View my orders** or **Orders**. Refresh the page; the confirmed order
   should persist. Placing an order reduces this demo store's stock.

## Test the manager journey

1. Open the PULSE dashboard URL and use its separate manager credentials.
2. Select **MIRA Dubai Marina** and the matching time window.
3. Review observed shopper demand, stockout evidence and perishable proposals.
   A shopper asking for a stocked product does not create an unresolved shortage;
   use an actually unavailable product to test that part of the loop.
4. Request the Google summary. It should summarize the displayed evidence.
5. Approve an action only if you intend to change the demo inventory or record
   that manager decision. Refresh and verify that the decision persists.

Forecast confidence and demand counts must follow available data. An empty panel
is valid when no matching events exist; the hosted deployment does not seed
fake shopper incidents or claim supplier delivery/payment integration.

## Operational checks

Requests to either agent URL without a Google identity token must be rejected.
The shopper URL without demo credentials must return an HTTP 401 challenge.
PULSE must show its sign-in form before loading manager data. Container and
application logs are available in Cloud Logging for each Cloud Run service.

For the unmet-demand demonstration, respond to ARIA's brown-rice alternative
with **Temporary compromise** or **Decline**. PULSE should show that explicit
feedback. A fulfilled or merely mentioned product should not be presented as an
unresolved need. Manager decisions affect the shared Google-backed catalog.
