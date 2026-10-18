# Contract and run-command audit

Audited October 18, 2026, after the unmet-demand changes were merged.

## Scope and evidence

This is a targeted source/API/behavior audit of the rewritten documentation,
not a claim that every sentence or every possible workflow was exhaustively verified.

| Area | Evidence checked | Result |
|---|---|---|
| Local run commands | scripts/run_local.py, Settings and DEPLOYMENT.md | Launcher sets both database paths; manual services must export matching absolute paths with different files |
| Four HTTP surfaces | FastAPI app.openapi() versus committed YAML | Request models and route snapshots match |
| Fifteen original tool signatures | Source AST versus individual spec Python signatures | Checked automatically for parameter/default/type parity |
| Shopper quote protocol | ARIA orchestration and integration tests | Current quote required; edited baskets/prices trigger review; session retry returns its order |
| Feedback and incident lifecycle | ARIA branches, logger and bridge upserts | Original intent persists; quote-only replies do not necessarily publish a new incident |
| Stock-check edge behavior | Direct calls against isolated in-memory fixtures | Known product at missing store returns unavailable; a raw proposed discount price can exist with active=false |
| Manager actions and observation | demand_intelligence.py and process/UI tests | Explicit-signal/source-safety gates and persisted decisions match the workflow specs |
| Cross-day discount replay | Simulated business-date change and new regression tests | Fixed a larger tier being applied under an old approval record |
| Integration boundaries | Endpoint handlers and Real* adapters | Google execution remains deferred; Python-only logger arguments remain absent from its HTTP request model |

## Corrections made

- Added a copy-ready common environment block to the root README. Both ARIA and
  PULSE need ARC_STATE_DB and ARC_BRIDGE_DB; a root .env is not loaded automatically.
- Corrected the stock-check specification: it validates nonempty IDs and global
  product existence, not independent store existence. Consumers must honor the
  discount_active flag rather than relying on discounted_price_aed being present.
- Replaced “all session transitions publish incidents” with the actual write
  points. session_logged reflects the last logging attempt, not every quote reply.
- Clarified that identical retries can return historical decided proposals;
  expiry rejection applies to undecided proposals that are no longer available.
- Fixed discount replay before re-evaluating a new tier. Approved batch percentages
  and displayed approved proposals now retain the original manager authorization.

## Boundaries that remain explicit

The local operational and incident stores are separate transactions. Analytics
publication needs an outbox in a production integration. Google model execution,
application authentication, supplier/logistics/payment integration and managed
cloud persistence remain outside the local prototype.

The legacy financial formula assumes a 48-hour source period, even when a caller
selects another dashboard window. It remains an illustrative scenario. The
feedback evaluation remains a curated synthetic development fixture, not a
held-out accuracy or measured business-impact study.

See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md),
[DATA_MODEL.md](../DATA_MODEL.md), [DEPLOYMENT.md](../DEPLOYMENT.md), and
[REVIEW_FIXES.md](REVIEW_FIXES.md) for the underlying contracts and limits.


## Validation of this follow-up

- All 15 original tool signatures match their specification ASTs.
- All four OpenAPI snapshots match the applications' generated schemas.
- All 212 checked local Markdown links resolve.
- Full available Python suite: 138 passed, one optional Streamlit dashboard module
  skipped because Streamlit is unavailable in this environment.
- Changed Python code passes Ruff and mypy. Four new parameterized cases cover
  approved/rejected discount retries the next day and after the proposal window.
