"""get_customer_context — SPEC-ARIA-02.

Retrieves the customer profile + last orders from AlloyDB (mock adapter).
Always called before building any cart.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Request
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.logger import get_logger
from tools.shared.rate_limit import limiter

logger = get_logger("aria.get_customer_context")
router = APIRouter()

# SPEC-ARIA-02: alphanumeric + underscore only.
_ID_FORMAT = re.compile(r"^[A-Za-z0-9_]+$")
_VALID_DIET = {"halal", "vegetarian", "vegan", "none"}


def get_customer_context(customer_id: str) -> dict:
    """
    Retrieves the customer's profile and last 3 orders from AlloyDB.
    Returns dietary_preference, weekly_budget_aed, household_size,
    preferred_store, last_orders list.
    Always call this before building any cart. Never skip this step.
    """
    # ── Input validation (SPEC-ARIA-02 §4) ───────────────────────────
    cid = (customer_id or "").strip()
    if len(cid) < 1:
        return error("VALIDATION_ERROR", "customer_id is empty")
    if len(cid) > 100:
        return error("VALIDATION_ERROR", "customer_id exceeds 100 chars")
    if not _ID_FORMAT.match(cid):
        return error("VALIDATION_ERROR", "customer_id must be alphanumeric + underscore")

    db = get_alloydb()
    customer = db.get_customer(cid)
    if not customer:
        return error("NOT_FOUND", f"customer {cid} not found")

    # ── Output sanity checks (SPEC-ARIA-02 §4) ───────────────────────
    dietary = customer["dietary_preference"]
    if dietary not in _VALID_DIET:
        return error("INTERNAL_ERROR", "invalid dietary_preference in profile")
    budget = float(customer["weekly_budget_aed"])
    if budget <= 0:
        return error("INTERNAL_ERROR", "weekly_budget_aed must be positive")
    household = int(customer["household_size"])
    if not (1 <= household <= 20):
        return error("INTERNAL_ERROR", "household_size out of range")

    # last_orders capped at the 3 most recent.
    last_orders = list(customer.get("last_orders", []))[:3]

    result = {
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "dietary_preference": dietary,
        "household_size": household,
        "weekly_budget_aed": budget,
        "preferred_store": customer["preferred_store"],
        "last_orders": last_orders,
    }
    # Privacy: never log name/email (SPEC-ARIA-02 §9). Log only id + counts.
    logger.info(
        "get_customer_context",
        tool="get_customer_context",
        customer_id=cid,
        orders_returned=len(last_orders),
        status="success",
    )
    return result


class CustomerContextRequest(BaseModel):
    customer_id: str


@router.post("/tools/get-customer-context")
@limiter.limit("60/minute")
async def get_customer_context_endpoint(request: Request, req: CustomerContextRequest) -> dict:
    return get_customer_context(req.customer_id)
