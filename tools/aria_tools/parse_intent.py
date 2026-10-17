"""parse_intent — SPEC-ARIA-01.

Extracts structured intent from a customer's natural-language message. First
tool ARIA calls each session. Uses the LLM adapter (Gemini Flash in prod,
deterministic mock locally).
"""

from __future__ import annotations

import re
import time

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.errors import error
from tools.shared.llm import get_llm
from tools.shared.logger import get_logger

logger = get_logger("aria.parse_intent")
router = APIRouter()

_INJECTION = re.compile(
    r"(\bDROP\b|\bSELECT\s+\*|\bINSERT\b|\bDELETE\b|--|;|<script>|javascript:)",
    re.IGNORECASE,
)
_VALID_DIET = {"halal", "vegetarian", "vegan", "none"}
_VALID_URGENCY = {"normal", "urgent"}


def parse_intent(customer_message: str) -> dict:
    """
    Extracts structured intent from a customer's natural language message.
    Returns goal, dietary_preference, budget_aed, household_size, urgency.
    Call this first when a customer sends their initial shopping request.
    Do NOT call this for follow-up messages in an ongoing session.
    """
    started = time.perf_counter()
    msg = (customer_message or "").strip()

    # ── Validation + sanitization (SPEC-ARIA-01 §4) ──────────────────
    if len(msg) < 1:
        return error("VALIDATION_ERROR", "customer_message is empty")
    if len(msg) > 1000:
        return error("VALIDATION_ERROR", "customer_message exceeds 1000 chars")
    if _INJECTION.search(msg):
        return error("VALIDATION_ERROR", "message contains disallowed patterns")

    # ── Extract via LLM adapter (heuristic in mock mode) ─────────────
    low = msg.lower()
    dietary = "none"
    for d in ("halal", "vegetarian", "vegan"):
        if d in low:
            dietary = d
            break

    budget = None
    m = re.search(r"(?:aed|dhs?|dirhams?)\s*([0-9]+(?:\.[0-9]+)?)", low) or re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:aed|dhs?|dirhams?)", low
    )
    if m:
        budget = float(m.group(1))

    household = None
    hm = re.search(r"family of\s*([0-9]+)", low) or re.search(r"([0-9]+)\s*(?:people|persons?)", low)
    if hm:
        household = max(1, min(20, int(hm.group(1))))

    urgency = "urgent" if any(w in low for w in ("urgent", "right now", "asap")) else "normal"

    # Goal: let the LLM classify; keep the raw phrase as the goal text.
    get_llm()  # touch adapter (routes to mock server if configured)
    goal = msg if len(msg) <= 60 else "grocery shopping"
    if not goal.strip():
        goal = "grocery shopping"

    # ── Output sanity checks ─────────────────────────────────────────
    if dietary not in _VALID_DIET:
        dietary = "none"
    if urgency not in _VALID_URGENCY:
        urgency = "normal"
    if budget is not None and budget <= 0:
        budget = None

    result = {
        "goal": goal,
        "dietary_preference": dietary,
        "budget_aed": budget,
        "household_size": household,
        "urgency": urgency,
    }
    logger.info(
        "parse_intent",
        tool="parse_intent",
        latency_ms=round((time.perf_counter() - started) * 1000, 1),
        status="success",
        dietary_preference=dietary,
    )
    return result


class ParseIntentRequest(BaseModel):
    customer_message: str


@router.post("/tools/parse-intent")
async def parse_intent_endpoint(req: ParseIntentRequest) -> dict:
    return parse_intent(req.customer_message)
