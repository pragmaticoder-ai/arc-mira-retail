# PULSE dashboard

Run the full shared-state prototype from the repository root:

```bash
.venv/bin/python scripts/run_local.py
```

PULSE opens at http://localhost:8501. Both operational and incident database
paths must match ARIA's environment; the launcher sets them automatically.
Standalone execution without paths uses isolated process memory and shows a warning.
The dashboard calls the PULSE tools directly. `PULSE_AGENT_URL` is not used.

Store and period selectors are functional. A Streamlit fragment refreshes the data
without blocking the app. Decisions are persisted before success is displayed;
failed writes show an error. See [the project README](../../README.md) for the
workflow and the Google integration boundary.
