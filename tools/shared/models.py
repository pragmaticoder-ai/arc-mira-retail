"""Shared Pydantic models for ARC tool functions.

These models define the input/output contracts for all tools,
ensuring type safety and validation across ARIA and PULSE agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Common Response Models ────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error response for all tools."""
    error: bool = True
    error_code: str
    error_message: str
    retry_suggested: bool = False


# ── ARIA Tools ─────────────────────────────────────────────────────

class ParseIntentRequest(BaseModel):
    customer_message: str = Field(..., min_length=1, max_length=1000)


class ParseIntentResponse(BaseModel):
    goal: str
    dietary_preference: str  # halal | vegetarian | vegan | none
    budget_aed: float | None = None
    household_size: int | None = None
    urgency: str = "normal"  # normal | urgent


class GetCustomerContextRequest(BaseModel):
    customer_id: str


class LastOrder(BaseModel):
    product_id: str
    product_name: str
    last_ordered: str


class GetCustomerContextResponse(BaseModel):
    customer_id: str
    name: str
    dietary_preference: str
    household_size: int
    weekly_budget_aed: float
    preferred_store: str
    last_orders: list[LastOrder] = []


class BuildCartRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=500)
    dietary_preference: str
    budget_aed: float = Field(..., gt=0, le=10000)
    household_size: int = Field(..., ge=1, le=20)
    store_id: str


class CartItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price_aed: float
    aisle_ref: str
    in_stock: bool


class UnavailableItem(BaseModel):
    product_id: str
    product_name: str


class BuildCartResponse(BaseModel):
    items: list[CartItem]
    total_aed: float
    items_unavailable: list[UnavailableItem] = []


class CheckStockRequest(BaseModel):
    product_id: str
    store_id: str


class AlternativeStore(BaseModel):
    store_id: str
    store_name: str
    quantity: int
    distance_km: float | None = None


class CheckStockResponse(BaseModel):
    product_id: str
    available: bool
    quantity: int
    aisle_ref: str
    alternative_stores: list[AlternativeStore] = []


class SuggestSubstitutionRequest(BaseModel):
    product_id: str
    store_id: str
    dietary_preference: str
    max_price_aed: float


class SuggestSubstitutionResponse(BaseModel):
    substitute_product_id: str
    name: str
    price_aed: float
    similarity_score: float
    reason: str
    in_stock: bool


class OptimizeBudgetRequest(BaseModel):
    cart: list[dict[str, Any]]
    target_budget_aed: float
    dietary_preference: str


class BudgetChange(BaseModel):
    action: str
    product_name: str
    saving_aed: float


class OptimizeBudgetResponse(BaseModel):
    updated_cart: list[dict[str, Any]]
    new_total_aed: float
    changes_made: list[BudgetChange] = []


class ApplyPromotionRequest(BaseModel):
    cart: list[dict[str, Any]]
    cart_total_aed: float
    dietary_preference: str
    store_id: str


class ApplyPromotionResponse(BaseModel):
    promotion_applied: bool
    promotion_id: str | None = None
    promotion_name: str | None = None
    discount_aed: float = 0.0
    new_total_aed: float
    reason: str = ""


class PlaceOrderRequest(BaseModel):
    customer_id: str
    store_id: str
    cart: list[dict[str, Any]]
    promotion_id: str | None = None
    total_aed: float


class PlaceOrderResponse(BaseModel):
    order_id: str
    status: str
    total_aed: float
    estimated_delivery_window: str


class LogSessionRequest(BaseModel):
    session_id: str
    customer_id: str
    store_id: str
    items_ordered: list[dict[str, Any]]
    items_unavailable: list[dict[str, Any]]
    substitutions: list[dict[str, Any]]
    promotion_id: str | None = None
    promotion_saving_aed: float = 0.0
    cart_total_aed: float
    budget_aed: float
    sentiment: str  # positive | neutral | negative
    order_placed: bool
    abandonment_reason: str | None = None


class LogSessionResponse(BaseModel):
    session_id: str
    logged: bool
    timestamp: str


# ── PULSE Tools ────────────────────────────────────────────────────

class DetectPatternsRequest(BaseModel):
    store_id: str
    hours: int = 48
    min_incidents: int = 5


class PatternEvidence(BaseModel):
    first_incident: str
    last_incident: str
    sample_session_ids: list[str]
    substitution_acceptance_rate: float


class StockoutPattern(BaseModel):
    product_id: str
    product_name: str
    store_id: str
    incident_count: int
    period_hours: int
    estimated_revenue_lost_aed: float
    peak_hour: str
    abandonment_count: int
    evidence: PatternEvidence


class DetectPatternsResponse(BaseModel):
    patterns: list[StockoutPattern] = []


class FindRootCauseRequest(BaseModel):
    product_id: str
    store_id: str
    peak_hour: str
    incident_count: int
    period_hours: int


class RootCauseEvidence(BaseModel):
    delivery_day: str
    delivery_time: str
    demand_peak_window: str
    gap_hours: int
    data_sources: list[str]


class FindRootCauseResponse(BaseModel):
    root_cause: str
    confidence_level: str  # High | Medium | Low
    explanation: str
    evidence: RootCauseEvidence
    recommended_action: str


class PredictStockoutRequest(BaseModel):
    product_id: str
    store_id: str
    forecast_days: int = 7


class PredictionEvidence(BaseModel):
    model: str
    training_period: str
    data_points_used: int


class PredictStockoutResponse(BaseModel):
    predicted_stockout_date: str
    days_until_stockout: int
    confidence: float
    current_stock: int
    daily_consumption_rate: float
    evidence: PredictionEvidence


class CalculateImpactRequest(BaseModel):
    product_id: str
    store_id: str
    incident_count: int
    average_cart_aed: float
    abandonment_count: int
    days_to_next_delivery: int


class ImpactEvidence(BaseModel):
    incidents_used: int
    average_cart_aed: float
    abandonment_rate: float
    formula: str


class CalculateImpactResponse(BaseModel):
    revenue_lost_aed: float
    revenue_at_risk_aed: float
    revenue_recoverable_aed: float
    calculation_basis: str
    evidence: ImpactEvidence


class DraftPurchaseOrderRequest(BaseModel):
    product_id: str
    store_id: str
    quantity: int
    urgency: str  # low | medium | high | critical
    justification: str
    revenue_at_risk_aed: float
    revenue_recoverable_aed: float
    evidence_summary: str


class DraftPurchaseOrderResponse(BaseModel):
    po_id: str
    product_id: str
    product_name: str
    quantity: int
    urgency: str
    justification: str
    revenue_at_risk_aed: float
    revenue_recoverable_aed: float
    evidence_summary: str
    status: str = "pending"
    human_approval_required: bool = True
    created_at: str


class ExecutePerishableDiscountRequest(BaseModel):
    store_id: str


class PerishableAlertEvidence(BaseModel):
    data_source: str
    expiry_source: str
    trigger_formula: str


class PerishableAlert(BaseModel):
    product_id: str
    product_name: str
    store_id: str
    stock_quantity: int
    expiry_date: str
    days_to_expiry: int
    daily_sales_rate: float
    projected_sell_through: int
    units_at_risk: int
    revenue_at_risk_aed: float
    discount_pct: float
    discounted_price_aed: float
    revenue_recoverable_aed: float
    evidence: PerishableAlertEvidence
    status: str = "pending"
    human_approval_required: bool = True


class ExecutePerishableDiscountResponse(BaseModel):
    perishable_alerts: list[PerishableAlert] = []
