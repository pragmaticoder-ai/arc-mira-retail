# PULSE dashboard — demo stand-in

> ⚠️ **Ownership note:** this is a frontend **demo stand-in** so the operations
> half of the ARC demo runs offline. The **backend engineer owns the production
> dashboard** wired to the real PULSE agent + AlloyDB/BigQuery (see
> ARCHITECTURE.md §9). Data shapes here follow `AGENT_CONTRACTS.md` so swapping
> to the real agent needs no reshaping.

## Run locally

```bash
cd frontend/pulse-dashboard
pip install -r requirements.txt
streamlit run pulse_dashboard.py
# → http://localhost:8501
```

## Configuration (env-backed → Secret Manager in Cloud Run)

| Variable | Default | Purpose |
|----------|---------|---------|
| `PULSE_AGENT_URL` | unset | Real PULSE agent URL. Unset → mock data. |
| `PULSE_STORE_NAME` | `MIRA Dubai Marina` | Store label. |
| `PULSE_REFRESH_SECONDS` | `10` | Auto-refresh cadence (demo moment). |

Nothing is hardcoded; all config comes from the environment.

## Demo moment

The dashboard auto-refreshes every 10 seconds. When ARIA logs a session to the
BigQuery bridge, the stockout alert appears within one refresh cycle, and
approving a PO flips its status live on screen (ARCHITECTURE.md §10.4).
