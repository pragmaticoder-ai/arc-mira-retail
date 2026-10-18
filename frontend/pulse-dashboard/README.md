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


The workspace shows explicit unmet-demand evidence, compares transfer/replenish/
defer options, persists manager decisions, and monitors later product-request
outcomes. It has no manager-login screen. Financial scenarios and synthetic seeds
remain labeled. See [SCREENS.md](../mira-brand/SCREENS.md) and
[SPEC-PULSE-08](../../specs/SPEC-PULSE-08-manager_decisions.md) for the implemented
approval and observation behavior.
