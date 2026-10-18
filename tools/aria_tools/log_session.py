"""log_session — SPEC-ARIA-09.

Writes the session summary to the BigQuery incidents bridge (mock adapter).
This is the ARIA->PULSE bridge. ALWAYS the final step of a session, even when
no order was placed. Idempotent on session_id.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel

from tools.shared.bigquery_client import get_bigquery
from tools.shared.clock import now
from tools.shared.errors import error
from tools.shared.logger import get_logger
from tools.shared.rate_limit import limiter

logger = get_logger("aria.log_session")
router = APIRouter()

_VALID_SENTIMENT = {"positive", "neutral", "negative"}


def log_session(
    session_id: str,
    customer_id: str,
    store_id: str,
    items_ordered: list[dict],
    items_unavailable: list[dict],
    substitutions: list[dict],
    promotion_id: str | None,
    promotion_saving_aed: float,
    cart_total_aed: float,
    budget_aed: float | None,
    sentiment: str,
    order_placed: bool,
    abandonment_reason: str | None = None,
    *, demand_signals: list[dict] | None = None, requested_items: list[str] | None = None,
) -> dict:
    """
    Writes the complete session summary to the BigQuery incidents table — the
    bridge between ARIA and PULSE. ALWAYS call this as the absolute last step,
    even if no order was placed. sentiment: positive | neutral | negative.
    """
    # ── Validation (SPEC-ARIA-09 §4) ─────────────────────────────────
    if not session_id:
        return error("VALIDATION_ERROR", "session_id is required")
    try:
        uuid.UUID(str(session_id))
    except (ValueError, AttributeError, TypeError):
        return error("VALIDATION_ERROR", "session_id must be a valid UUID")
    if sentiment not in _VALID_SENTIMENT:
        return error("VALIDATION_ERROR", f"invalid sentiment: {sentiment}")
    if (promotion_saving_aed or 0) < 0:
        return error("VALIDATION_ERROR", "promotion_saving_aed must be >= 0")
    if (cart_total_aed or 0) < 0:
        return error("VALIDATION_ERROR", "cart_total_aed must be >= 0")
    if budget_aed is not None and budget_aed < 0:
        return error("VALIDATION_ERROR", "budget_aed must be >= 0")

    incident: dict = {
        "session_id": session_id,
        "customer_id": customer_id,
        "store_id": store_id,
        "timestamp": now().isoformat(),
        "demand_signals": demand_signals or [],
        "requested_items": requested_items or [],
        "session_status": "completed" if order_placed else "abandoned" if abandonment_reason else "active",
        "items_ordered": items_ordered or [],
        "items_unavailable": items_unavailable or [],
        "substitutions_offered": substitutions or [],
        "promotion_id": promotion_id,
        "promotion_saving_aed": promotion_saving_aed or 0.0,
        "cart_total_aed": cart_total_aed or 0.0,
        "budget_aed": budget_aed,
        "session_sentiment": sentiment,
        "order_placed": bool(order_placed),
        "abandonment_reason": abandonment_reason,
    }
    from tools.shared.demand import OUTCOMES
    if any(s.get("outcome") not in OUTCOMES or not s.get("product_id") for s in incident["demand_signals"]):
        return error("VALIDATION_ERROR", "Invalid demand evidence")
    res = get_bigquery().insert_incident(incident)
    logger.info(
        "log_session",
        tool="log_session",
        session_id=session_id,
        order_placed=bool(order_placed),
        unavailable=len(items_unavailable or []),
        status="success",
    )
    return {"session_id": res["session_id"], "logged": res["logged"], "timestamp": res["timestamp"]}


class LogSessionRequest(BaseModel):
    session_id: str
    customer_id: str
    store_id: str
    items_ordered: list[dict] = []
    items_unavailable: list[dict] = []
    substitutions: list[dict] = []
    promotion_id: str | None = None
    promotion_saving_aed: float = 0.0
    cart_total_aed: float = 0.0
    budget_aed: float | None = None
    sentiment: str = "neutral"
    order_placed: bool = False
    abandonment_reason: str | None = None


@router.post("/tools/log-session")
@limiter.limit("60/minute")
async def log_session_endpoint(request: Request, req: LogSessionRequest) -> dict:
    return log_session(
        req.session_id, req.customer_id, req.store_id, req.items_ordered,
        req.items_unavailable, req.substitutions, req.promotion_id,
        req.promotion_saving_aed, req.cart_total_aed, req.budget_aed,
        req.sentiment, req.order_placed, req.abandonment_reason,
    )
