# PULSE operations dashboard

Run `.venv/bin/python scripts/run_local.py` from the repository root for local apps using Google infrastructure. PULSE opens at http://localhost:8501. `USE_MOCK=true` is an explicit offline testing option; shared SQLite needs both `ARC_STATE_DB` and `ARC_BRIDGE_DB` paths.

Hosted access uses a branded manager form with a store selector. Credentials are in the ignored `data/local/cloud/ACCESS.md`. Sign out is in the sidebar.

Pages: Overview, Unmet demand, Stockout alerts, Perishables, Customer activity, Action history. Store, period, refresh, drill-in, decisions, and history filters are functional. Overview charts show recorded hourly request activity, product-intent outcomes, and separately labeled modeled exposure. Synthetic evidence remains labeled. Completed-action counts and history cover all persisted store decisions; demand metrics use the selected period.

Discount approvals change shared prices. Transfers move shared stock above source safety levels. **Approve & restock (demo)** approves a PO and simulates receipt once, atomically; demand replenishment approval performs the same receipt. It contacts no supplier. Rejection leaves prices and inventory unchanged. History retains decisions after active alerts clear; feedback confirms a successful write and failures display an error.

The dashboard calls shared operational tools directly; `PULSE_AGENT_URL` is used for the optional Google analysis summary, authenticated with its Cloud Run service identity. Shopper activity comes from persisted ARIA sessions; approved changes are visible in subsequent ARIA interactions and newly fetched catalog pages. Existing checkout quotes are revalidated before an order can be placed.
