"""Shared Pydantic models for ARC tools — SPEC-00 §4.

Mirror AGENT_CONTRACTS.md I/O shapes and DATA_MODEL.md tables. Tool functions
return plain dicts (per CONTRIBUTING.md), but these models validate and
document the shapes and are reused by tests (contract validation).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────
class DietaryPreference(StrEnum):
    halal = "halal"
    vegetarian = "vegetarian"
    vegan = "vegan"
    none = "none"


class Sentiment(StrEnum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class Urgency(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Confidence(StrEnum):
    high = "High"
    medium = "Medium"
    low = "Low"


# ── Standard error response (AGENT_CONTRACTS.md) ─────────────────────
class ErrorResponse(BaseModel):
    error: bool = True
    error_code: str
    error_message: str
    retry_suggested: bool = False


# ── ARIA I/O models ──────────────────────────────────────────────────
class ParseIntentResponse(BaseModel):
    goal: str
    dietary_preference: DietaryPreference
    budget_aed: float
    household_size: int
    urgency: str


class LastOrder(BaseModel):
    product_id: str
    product_name: str
    last_ordered: str


class CustomerContextResponse(BaseModel):
    customer_id: str
    name: str
    dietary_preference: str
    household_size: int
    weekly_budget_aed: float
    preferred_store: str
    last_orders: list[LastOrder] = Field(default_factory=list)


class CartItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price_aed: float
    aisle_ref: str
    in_stock: bool
    substituted: bool = False
    discount_active: bool = False


class UnavailableItem(BaseModel):
    product_id: str
    product_name: str


class BuildCartResponse(BaseModel):
    items: list[CartItem]
    total_aed: float
    items_unavailable: list[UnavailableItem] = Field(default_factory=list)


class AlternativeStore(BaseModel):
    store_id: str
    store_name: str
    quantity: int
    distance_km: float = 0.0


class CheckStockResponse(BaseModel):
    product_id: str
    available: bool
    quantity: int
    aisle_ref: str
    discount_active: bool = False
    discounted_price_aed: float | None = None
    alternative_stores: list[AlternativeStore] = Field(default_factory=list)


class SubstitutionResponse(BaseModel):
    substitute_product_id: str | None
    name: str | None
    price_aed: float | None
    similarity_score: float | None
    reason: str
    in_stock: bool


class BudgetChange(BaseModel):
    action: str
    product_name: str
    saving_aed: float


class OptimizeBudgetResponse(BaseModel):
    updated_cart: list[CartItem]
    new_total_aed: float
    changes_made: list[BudgetChange] = Field(default_factory=list)


class ApplyPromotionResponse(BaseModel):
    promotion_applied: bool
    promotion_id: str | None = None
    promotion_name: str | None = None
    discount_aed: float = 0.0
    new_total_aed: float
    reason: str = ""


class PlaceOrderResponse(BaseModel):
    order_id: str
    status: str
    total_aed: float
    estimated_delivery_window: str


class LogSessionResponse(BaseModel):
    session_id: str
    logged: bool
    timestamp: str


# ── PULSE I/O models ──────────────────────────────────────────────────
class PatternEvidence(BaseModel):
    first_incident: str
    last_incident: str
    sample_session_ids: list[str] = Field(default_factory=list)
    substitution_acceptance_rate: float = 0.0


class StockoutPattern(BaseModel):
    product_id: str
    product_name: str
    store_id: str
    incident_count: int
    period_hours: int
    estimated_revenue_lost_aed: float
    peak_hour: str = ""
    abandonment_count: int = 0
    average_cart_aed: float = 0.0
    evidence: PatternEvidence | None = None


class DetectPatternsResponse(BaseModel):
    patterns: list[StockoutPattern] = Field(default_factory=list)


class RootCauseResponse(BaseModel):
    root_cause: str
    confidence_level: Confidence
    explanation: str
    evidence: dict
    recommended_action: str


class PredictStockoutResponse(BaseModel):
    predicted_stockout_date: str
    days_until_stockout: int
    confidence: float
    current_stock: int
    daily_consumption_rate: float
    evidence: dict


class CalculateImpactResponse(BaseModel):
    revenue_lost_aed: float
    revenue_at_risk_aed: float
    revenue_recoverable_aed: float
    calculation_basis: str
    evidence: dict


class DraftPOResponse(BaseModel):
    po_id: str
    product_id: str
    product_name: str
    quantity: int
    urgency: Urgency
    justification: str
    revenue_at_risk_aed: float
    revenue_recoverable_aed: float
    evidence_summary: str
    status: str = "pending"
    human_approval_required: bool = True
    created_at: str
