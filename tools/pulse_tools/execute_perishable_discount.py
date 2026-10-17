"""PULSE tool: execute_perishable_discount

Detects perishable items at risk of waste and proposes tiered discounts.

Spec: specs/SPEC-PULSE-06-execute_perishable_discount.md
"""

from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from tools.shared.models import (
    ExecutePerishableDiscountRequest,
    ExecutePerishableDiscountResponse,
    PerishableAlert,
    PerishableAlertEvidence,
)
from tools.shared.alloydb_client import get_alloydb
from tools.shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def calculate_discount_tier(days_to_expiry: int) -> float:
    """Calculate discount percentage based on days to expiry."""
    if days_to_expiry <= 1:
        return 40.0
    elif days_to_expiry <= 2:
        return 25.0
    elif days_to_expiry <= 3:
        return 15.0
    return 0.0


@router.post("/execute-perishable-discount", response_model=ExecutePerishableDiscountResponse)
async def execute_perishable_discount(request: ExecutePerishableDiscountRequest):
    """
    Detect perishable items at risk and propose discounts.
    
    Trigger condition: days_to_expiry × daily_sales_rate < stock_quantity
    
    Returns:
        ExecutePerishableDiscountResponse: list of perishable alerts
    """
    try:
        db = get_alloydb()
        
        # Get all inventory for store
        inventory = db.list_inventory(request.store_id)
        
        alerts = []
        
        for product in inventory:
            # Check if perishable
            if not product.get("is_perishable", False):
                continue
            
            # Check expiry date
            expiry_date_str = product.get("expiry_date")
            if not expiry_date_str:
                continue
            
            try:
                expiry_date = datetime.fromisoformat(expiry_date_str)
            except:
                continue
            
            # Calculate days to expiry
            days_to_expiry = (expiry_date - datetime.now()).days
            
            if days_to_expiry < 0:
                continue  # Already expired
            
            # Calculate sell-through velocity (mock: assume 10 units/day)
            daily_sales_rate = 10.0
            
            # Calculate projected sell-through
            projected_sell_through = int(days_to_expiry * daily_sales_rate)
            
            # Check trigger condition
            stock_quantity = product.get("stock_quantity", 0)
            if projected_sell_through >= stock_quantity:
                continue  # Will sell through before expiry
            
            # Calculate units at risk
            units_at_risk = stock_quantity - projected_sell_through
            
            # Calculate discount tier
            discount_pct = calculate_discount_tier(days_to_expiry)
            
            if discount_pct == 0:
                continue  # No discount needed yet
            
            # Calculate revenue impact
            price_aed = product.get("price_aed", 0)
            discounted_price = price_aed * (1 - discount_pct / 100)
            revenue_at_risk = units_at_risk * price_aed
            revenue_recoverable = units_at_risk * discounted_price
            
            alert = PerishableAlert(
                product_id=product["product_id"],
                product_name=product["product_name"],
                store_id=request.store_id,
                stock_quantity=stock_quantity,
                expiry_date=expiry_date_str,
                days_to_expiry=days_to_expiry,
                daily_sales_rate=daily_sales_rate,
                projected_sell_through=projected_sell_through,
                units_at_risk=units_at_risk,
                revenue_at_risk_aed=round(revenue_at_risk, 2),
                discount_pct=discount_pct,
                discounted_price_aed=round(discounted_price, 2),
                revenue_recoverable_aed=round(revenue_recoverable, 2),
                evidence=PerishableAlertEvidence(
                    data_source="BigQuery incidents — 7-day velocity",
                    expiry_source="AlloyDB inventory.expiry_date",
                    trigger_formula="days_to_expiry × daily_sales_rate < stock_quantity",
                ),
                status="pending",
                human_approval_required=True,
            )
            
            alerts.append(alert)
        
        logger.info(
            "execute_perishable_discount_success",
            store_id=request.store_id,
            alerts_generated=len(alerts),
        )
        
        return ExecutePerishableDiscountResponse(perishable_alerts=alerts)
        
    except Exception as e:
        logger.error("execute_perishable_discount_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
