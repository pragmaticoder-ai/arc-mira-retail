# Feedback evaluation

Run `.venv/bin/python -m scripts.evaluate_demand` from the repository root.

The committed fixture contains **20 curated synthetic English examples** covering
satisfied alternatives, temporary compromises, rejection, abandonment and unknown
feedback. The baseline maps accepted alternatives to satisfied and everything
else to rejected. ARC uses the deterministic rule parser exercised by the local
shopper workflow.

On these examples, the baseline matches **10/20** labels; the rule parser matches
**20/20**, including all **5** explicit compromise examples. The command computes
these numbers from the fixture; they are not hardcoded in the report.

This is a small development fixture, not a held-out evaluation or representative
customer dataset. The examples informed the supported phrase patterns. These
results demonstrate why preserving the distinction matters; they do not establish
production accuracy, business lift, or superiority to another deployed system.
A future model integration should use independent annotation, a held-out set,
negation and ambiguity cases, more languages, and per-outcome precision/recall.

Functional evidence is separate: regression tests exercise checkout, incident
updates, manager approval, separate-process visibility and subsequent fulfillment.
The dashboard's before/after counts are observations, not a causal experiment.
