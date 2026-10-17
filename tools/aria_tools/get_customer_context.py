"""get_customer_context — SPEC-ARIA-02.

Retrieves the customer profile + last orders from AlloyDB (mock adapter).
Always called before building any cart.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.logger import get_logger

logger = get_logger("aria.get_customer_context")
router = APIRouter()


def get_customer_context(customer_id: str) -> dict:
    """
    Retrieves the customer's profile and last 3 orders from AlloyDB.
    Returns dietary_preference, weekly_budget_aed, household_size,
    preferred_store, last_orders list.
    Always call this before building any cart. Never skip this step.
    """
    db = get_alloydb()
    customer = db.get_customer(customer_id)
    if not customer:
        return error("NOT_FOUND", f"customer {customer_id} not found")

    result = {
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "dietary_preference": customer["dietary_preference"],
        "household_size": customer["household_size"],
        "weekly_budget_aed": float(customer["weekly_budget_aed"]),
        "preferred_store": customer["preferred_store"],
        "last_orders": customer.get("last_orders", []),
    }
    logger.info("get_customer_context", tool="get_customer_context", status="success")
    return result


class CustomerContextRequest(BaseModel):
    customer_id: str


@router.post("/tools/get-customer-context")
async def get_customer_context_endpoint(req: CustomerContextRequest) -> dict:
    return get_customer_context(req.customer_id)
