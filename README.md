# ARC — Agentic Retail Command

ARC connects **ARIA**, a grocery shopping assistant, with **PULSE**, a store operations dashboard. Customer preferences and unmet needs remain visible even when a shopper accepts a temporary alternative. A manager reviews the evidence, approves an action, and sees subsequent shopper outcomes.

**Team:** Pragmatic Engineers · **Theme:** Retail & Commerce

## Try the hosted demo

No installation or signup is required.

| Application | Link | Sign-in |
|---|---|---|
| ARIA — customer shopping | [Open ARIA](https://arc-storefront-kif65kxodq-as.a.run.app/login) | Choose a customer below and enter the shared shopper password |
| PULSE — manager operations | [Open PULSE](https://arc-pulse-dashboard-kif65kxodq-as.a.run.app) | Username: `pulse-manager` · Password: `Mira2026!` |

### Customer accounts

**Shared ARIA password for all five customers: `Mira2026!`**

| Customer | Username | Household size | Dietary preference | Weekly budget |
|---|---|---|---|---|
| Sarah | `mira-demo` | 4 | Halal | AED 300 |
| Ahmed | `ahmed-demo` | 1 | None | AED 150 |
| Fatima | `fatima-demo` | 3 | Vegetarian | AED 250 |
| Kumar | `kumar-demo` | 2 | None | AED 200 |
| Layla | `layla-demo` | 5 | Halal | AED 400 |

On ARIA's login page, select the customer's name from **Demo customer**, enter the shared password, and click **Sign in**. Sarah corresponds to `mira-demo`; the picker shows names and household preferences rather than requiring you to type usernames.

Each customer has separate conversations, baskets and order history. Open the avatar menu to choose **My orders**, **Switch customer**, or **Sign out**. Switching customer returns you to the login page; that customer's basket and conversation are retained in the same browser session.

For PULSE, enter `pulse-manager` and its password above, select **MIRA Dubai Marina**, and click **Access dashboard**. Use the **PM** avatar or sidebar **Sign out** to end the manager session.

These published credentials are for the fictional hackathon demo only. They are application credentials, not Google Cloud or database credentials. The ignored owner access file is `data/local/cloud/ACCESS.md`; update this section if demo passwords are rotated. Cloud Run scales to zero, so the first visit may take longer.

## Judge walkthrough

1. Sign into ARIA as **Sarah**. Ask: **“Weekly halal groceries, family of 4, AED 300. Include brown rice.”**
2. Review the actual basket total and any unavailable-product explanation. Brown rice starts unavailable unless a manager has already restocked it. Choose **Temporary compromise** or **Decline** on an offered alternative to record your preference.
3. Open the cart icon, adjust quantities if needed, click **Review updated basket**, then **Confirm order** after reviewing the quote. Check **My orders** for the confirmed order.
4. Sign into PULSE for the same store. **Overview** shows request activity, demand outcomes, modeled exposure and recent decisions. **Unmet demand** shows customer evidence and transfer/replenish/defer choices.
5. Review a stockout alert and click **Approve & restock (demo)**, or approve an available transfer. PO approval simulates receipt once; transfers preserve source safety stock. Discount approval changes the shared catalog price. No supplier is contacted.
6. Check the success feedback and **Action history** for completed, approved, rejected or monitoring decisions. Rejected actions leave stock and prices unchanged. History remains visible after an alert clears.
7. In ARIA, request the affected product again, using the same customer or **Switch customer**. The next interaction reads the updated stock or price. Refresh the catalog to see approved offers.
8. Use PULSE's **Customer activity** page to distinguish shopper sessions, baskets and orders. After-decision outcomes are observations; exposure charts are estimates, not measured recovered revenue. Synthetic seed evidence is labeled.

Catalog search, categories, attribute facets, sorting, pagination, product details, approved Offers, basket navigation and order history are functional. Halal filtering applies to meat; rice and seafood do not require a halal meat label.

See the [demo guide](docs/DEMO.md), [UI verification coverage](docs/UI_QA.md), and [Cloud Run deployment guide](docs/CLOUD_RUN.md).

## Run locally with Google infrastructure

Use Python 3.11+ and Node 18.17+ with npm. Follow [LOCAL_GOOGLE.md](docs/LOCAL_GOOGLE.md) for Google CLI/ADC and environment configuration, then run:

```bash
uv sync --group dev
npm --prefix frontend/aria-app ci
.venv/bin/python scripts/run_local.py
```

Open ARIA at **http://localhost:3000** and PULSE at **http://localhost:8501**. The launcher defaults to Google mode: Gemini on Vertex AI, Cloud SQL PostgreSQL operational state, and BigQuery incident evidence. It starts the agent services and stops its child processes on Ctrl+C. Google credentials stay in the backend; the storefront calls its ARIA API proxy.

Create missing fictional customer profiles against the configured Google database without overwriting existing profiles:

```bash
.venv/bin/python scripts/create_demo_customers.py
```

Hosted demo sign-in is enabled by the deployment's environment settings. Local authentication is optional; the hosted account instructions above describe the deployed applications.

### Explicit offline test mode

To run the older rules/SQLite fixture demo without Google services:

```bash
.venv/bin/python scripts/run_local.py --offline --data-dir /tmp/arc-fresh-demo
```

Offline mode uses synthetic fixtures and deterministic rules. Its operational and incident SQLite files must be separate, and their paths must match across app processes. This is a single-host test option; the hosted services use Google infrastructure.

If usual ports are occupied, add `--web-port 3100 --aria-port 8003 --pulse-port 8502`. See [DEPLOYMENT.md](DEPLOYMENT.md) for additional run commands.

## Validate

```bash
.venv/bin/python -m pytest
npm --prefix frontend/aria-app test
npm --prefix frontend/aria-app run build
```

The current release passed 182 Python tests, 12 frontend tests and the Next.js production build. The hosted smoke test verified form authentication/customer scoping, the 4,145-product catalog, weekly shopping, explicit substitution feedback, checkout/order history/idempotency and Google analysis. Its temporary test records were removed and stock restored.

For a configured deployment, `.venv/bin/python scripts/smoke_cloud.py` runs the hosted smoke test using the ignored local access file. [UI_QA.md](docs/UI_QA.md) describes coverage and the limits of visual/device testing.

## Specifications

[ARC_SPEC.md](ARC_SPEC.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DATA_MODEL.md](DATA_MODEL.md), [AGENT_CONTRACTS.md](AGENT_CONTRACTS.md) and the [specification index](specs/README.md) document the system. For the current hosted setup and demo receipt behavior, use [CLOUD_RUN.md](docs/CLOUD_RUN.md) and [SPEC-PULSE-08](specs/SPEC-PULSE-08-manager_decisions.md). Older local-only descriptions in other documents may predate the Google deployment.
