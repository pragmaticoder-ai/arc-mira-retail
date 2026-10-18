# ARC tools and local adapters

The nine ARIA and six original PULSE tool functions are implemented. Demand
intelligence adds evidence aggregation, action comparison, manager decisions and
outcome monitoring. Tool functions return plain dictionaries.

`USE_MOCK=true` selects deterministic local implementations. Configure separate
`ARC_STATE_DB` and `ARC_BRIDGE_DB` files for cross-process operation; without
paths the adapters use isolated process memory for tests. `scripts/run_local.py`
sets the paths for all apps. Operational writes use SQLite transactions and
idempotency records. Customer evidence is upserted by session ID in the bridge.

The `Real*` Google adapters and ADK Runner execution are deferred. Setting
`USE_MOCK=false` does not provide a working cloud implementation. TF-IDF product
similarity and rule-based intent parsing are labeled local behavior, not Gemini.

See [the root README](../README.md) and [review fixes](../docs/REVIEW_FIXES.md).
