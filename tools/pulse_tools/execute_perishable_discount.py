"""execute_perishable_discount — SPEC-PULSE-06.

Detects perishable items whose sell-through velocity won't clear stock before
expiry, and proposes a tiered discount for manager approval. Never auto-applies.

Trigger:  days_to_expiry × daily_sales_rate < stock_quantity
Tiers:    3 days → 15% · 2 days → 25% · 1 day → 40%
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.bigquery_client import get_bigquery
from tools.shared.errors import error
from tools.shared.logger import get_logger

logger = get_logger("pulse.execute_perishable_discount")
router = APIRouter()

# Reference "today" for the demo so the seeded expiry dates trigger predictably.
_TODAY = date(2026, 10, 17)
_CONVERSION = 0.60  # expected sell-through lift from the discount
_TIERS = {1: 40.0, 2: 25.0, 3: 15.0}


def _days_to_expiry(expiry: str | None) -> int | None:
    if not expiry:
        return None
    try:
        d = date.fromisoformat(expiry)
    except ValueError:
        return None
    return (d - _TODAY).days


def execute_perishable_discount(store_id: str) -> dict:
    """
    Checks perishable inventory where current sell-through velocity will not
    clear stock before expiry (days_to_expiry × daily_sales_rate < stock).
    Proposes a tiered discount for manager approval. Never auto-applies;
    human approval is always required. Returns perishable_alerts (may be empty).
    """
    if not store_id or not store_id.strip():
        return error("VALIDATION_ERROR", "store_id is required")

    db = get_alloydb()
    inv = db.list_inventory(store_id)
    if inv is None:
        return error("NOT_FOUND", f"store {store_id} not found")

    bq = get_bigquery()
    alerts = []

    for p in inv:
        if not p.get("is_perishable") or p.get("stock_quantity", 0) <= 0:
            continue
        dte = _days_to_expiry(p.get("expiry_date"))
        if dte is None or dte < 1 or dte > 3:
            continue

        rate = bq.get_daily_sales_rate(product_id=p["product_id"], store_id=store_id)
        projected = int(dte * rate)
        stock = p["stock_quantity"]
        if projected >= stock:  # will clear in time → no action
            continue

        units_at_risk = stock - projected
        price = float(p["price_aed"])
        discount_pct = _TIERS[dte]
        discounted_price = round(price * (1 - discount_pct / 100.0), 2)
        revenue_at_risk = round(units_at_risk * price, 2)
        expected_additional = units_at_risk * _CONVERSION
        revenue_recoverable = round(min(expected_additional * discounted_price, revenue_at_risk), 2)

        alerts.append(
            {
                "product_id": p["product_id"],
                "product_name": p["product_name"],
                "store_id": store_id,
                "stock_quantity": stock,
                "expiry_date": p["expiry_date"],
                "days_to_expiry": dte,
                "daily_sales_rate": rate,
                "projected_sell_through": projected,
                "units_at_risk": units_at_risk,
                "revenue_at_risk_aed": revenue_at_risk,
                "discount_pct": discount_pct,
                "discounted_price_aed": discounted_price,
                "revenue_recoverable_aed": revenue_recoverable,
                "evidence": {
                    "data_source": "BigQuery incidents — 7-day velocity",
                    "expiry_source": "AlloyDB inventory.expiry_date",
                    "trigger_formula": f"{dte} × {rate} = {projected} < {stock} units in stock",
                },
                "status": "pending",
                "human_approval_required": True,
            }
        )

    logger.info(
        "execute_perishable_discount",
        tool="execute_perishable_discount",
        store_id=store_id,
        items_checked=len(inv),
        alerts_generated=len(alerts),
        status="success",
    )
    return {"perishable_alerts": alerts}


class PerishableDiscountRequest(BaseModel):
    store_id: str


@router.post("/tools/execute-perishable-discount")
async def execute_perishable_discount_endpoint(req: PerishableDiscountRequest) -> dict:
    return execute_perishable_discount(req.store_id)
