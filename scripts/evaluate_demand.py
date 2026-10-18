"""Report a reproducible curated synthetic comparison, not a model benchmark."""
from __future__ import annotations

import json
from pathlib import Path

from tools.shared.demand import classify_feedback


def evaluate() -> dict:
    cases = json.loads((Path(__file__).resolve().parents[1] / "tests/fixtures/demand_feedback.json").read_text())
    results = [{**case, "predicted": classify_feedback(case["message"]),
                "baseline": "satisfied" if case["accepted"] else "rejected"} for case in cases]
    return {"dataset": "20 curated synthetic English examples; not held-out or representative customer data",
            "method": "Deterministic rules; baseline assumes acceptance means satisfaction",
            "cases": len(results),
            "rules_correct": sum(r["predicted"] == r["expected"] for r in results),
            "baseline_correct": sum(r["baseline"] == r["expected"] for r in results),
            "explicit_compromises_detected": sum(r["expected"] == r["predicted"] == "compromise" for r in results),
            "failures": [r for r in results if r["predicted"] != r["expected"]]}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
