"""Evidence-backed substitution outcomes for the offline prototype.

This deliberately conservative rule parser is not Gemini. Unknown wording stays
unknown; explicit UI feedback is preferred. A future model can emit this schema.
"""
from __future__ import annotations

import re

OUTCOMES = {"satisfied", "compromise", "rejected", "abandoned", "fulfilled", "unknown"}


def classify_feedback(message: str) -> str:
    text = message.lower().replace("’", "'")
    if re.search(r"\b(cancel|leave|abandon)\b", text):
        return "abandoned"
    if any(p in text for p in ("no thanks", "no thank you", "not happy", "not satisfied", "doesn't work", "don't want", "do not want", "no substitute", "only brown rice", "reject")):
        return "rejected"
    if any(p in text for p in ("this time", "for now", "next time", "next week", "still prefer", "temporary", "compromise")):
        return "compromise"
    if any(p in text for p in ("happy with", "works for me", "equally good", "prefer the substitute", "satisfied", "great alternative")):
        return "satisfied"
    return "unknown"


def signal(product: dict, outcome: str, evidence: str, substitute_id: str | None = None) -> dict:
    if outcome not in OUTCOMES:
        raise ValueError("Unknown demand outcome")
    return {"product_id": product["product_id"], "product_name": product["product_name"],
            "outcome": outcome, "substitute_product_id": substitute_id,
            "evidence": evidence[:1000], "evidence_source": "customer_statement" if evidence else "unknown",
            "certainty": "explicit" if outcome != "unknown" else "unknown"}


def outcome_counts(signals: list[dict]) -> dict:
    counts = {name: 0 for name in sorted(OUTCOMES)}
    for item in signals:
        if item.get("outcome") in counts:
            counts[item["outcome"]] += 1
    counts["unresolved"] = sum(counts[k] for k in ("compromise", "rejected", "abandoned"))
    return counts
