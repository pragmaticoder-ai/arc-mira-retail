"""Verify culinary equivalence after vector retrieval and hard catalog filters."""

from __future__ import annotations

import json

from pydantic import BaseModel

from tools.shared.llm import get_llm


class SubstituteMatch(BaseModel):
    product_id: str | None
    explanation: str


def choose_substitute(original: dict, candidates: list[dict]) -> SubstituteMatch:
    prompt = (
        "Select a practical substitute for the original grocery product from the candidates. "
        "The same brand or broad category alone is not sufficient: preserve the food's identity "
        "and culinary role. For example, another rice can be offered for brown rice with the "
        "difference disclosed; lentils, flour or sugar are not rice substitutes. Choose null "
        "if none is a reasonable substitute. Stock, diet and maximum price were already filtered. "
        "Return only the structured result, using a supplied ID or null. Explain the actual "
        "difference briefly; do not invent product attributes or customer consent.\n"
        + json.dumps(
            {
                "original": {
                    k: original[k] for k in ("product_id", "product_name", "category")
                },
                "candidates": candidates,
            }
        )
    )
    match = SubstituteMatch.model_validate_json(
        get_llm().generate(
            prompt,
            response_mime_type="application/json",
            response_schema=SubstituteMatch,
            max_output_tokens=512,
            thinking_config={"thinking_budget": 0},
        )
    )
    if match.product_id is not None and match.product_id not in {
        c["product_id"] for c in candidates
    }:
        raise ValueError(
            "Google selected a substitute outside the retrieved catalog candidates"
        )
    return match
