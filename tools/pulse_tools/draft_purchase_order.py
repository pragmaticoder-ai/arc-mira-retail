"""draft_purchase_order — SPEC-PULSE-05.

Creates a PENDING purchase order in AlloyDB. Never auto-approves — human
approval is always required. Only called after calculate_impact().
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.logger import get_logger

logger = get_logger("pulse.draft_purchase_order")
router = APIRouter()

_VALID_URGENCY = {"low", "medium", "high", "critical"}


def draft_purchase_order(
    product_id: str,
    store_id: str,
    quantity: int,
    urgency: str,
    justification: str,
    revenue_at_risk_aed: float,
    revenue_recoverable_aed: float,
    evidence_summary: str,
) -> dict:
    """
    Creates a pending purchase order in AlloyDB purchase_orders. The PO stays
    PENDING until the manager approves/rejects — the system never auto-approves.
    Only call after calculate_impact().
    """
    # ── Validation (SPEC-PULSE-05 §4) ────────────────────────────────
    if not (1 <= quantity <= 10000):
        return error("VALIDATION_ERROR", "quantity must be 1..10000")
    if urgency not in _VALID_URGENCY:
        return error("VALIDATION_ERROR", f"invalid urgency: {urgency}")
    if not (justification or "").strip():
        return error("VALIDATION_ERROR", "justification is required")
    if len(justification) > 1000:
        return error("VALIDATION_ERROR", "justification exceeds 1000 chars")
    if not (evidence_summary or "").strip():
        return error("VALIDATION_ERROR", "evidence_summary is required")
    if len(evidence_summary) > 500:
        return error("VALIDATION_ERROR", "evidence_summary exceeds 500 chars")
    if revenue_at_risk_aed < 0 or revenue_recoverable_aed < 0:
        return error("VALIDATION_ERROR", "revenue figures must be >= 0")

    db = get_alloydb()
    product = db.get_product(product_id)
    if not product:
        return error("NOT_FOUND", f"product {product_id} not found")

    po = db.insert_purchase_order(
        {
            "product_id": product_id,
            "store_id": store_id,
            "supplier_id": product.get("supplier_id"),
            "quantity": quantity,
            "urgency": urgency,
            "justification": justification,
            "revenue_at_risk_aed": round(revenue_at_risk_aed, 2),
        }
    )
    result = {
        "po_id": po["po_id"],
        "product_id": product_id,
        "product_name": product["product_name"],
        "quantity": quantity,
        "urgency": urgency,
        "justification": justification,
        "revenue_at_risk_aed": round(revenue_at_risk_aed, 2),
        "revenue_recoverable_aed": round(revenue_recoverable_aed, 2),
        "evidence_summary": evidence_summary,
        "status": "pending",
        "human_approval_required": True,
        "created_at": po["created_at"],
    }
    logger.info(
        "draft_purchase_order",
        tool="draft_purchase_order",
        po_id=po["po_id"],
        product_id=product_id,
        status="pending",
    )
    return result


class DraftPORequest(BaseModel):
    product_id: str
    store_id: str
    quantity: int
    urgency: str
    justification: str
    revenue_at_risk_aed: float
    revenue_recoverable_aed: float
    evidence_summary: str


@router.post("/tools/draft-purchase-order")
async def draft_purchase_order_endpoint(req: DraftPORequest) -> dict:
    return draft_purchase_order(
        req.product_id, req.store_id, req.quantity, req.urgency, req.justification,
        req.revenue_at_risk_aed, req.revenue_recoverable_aed, req.evidence_summary,
    )
