"""predict_stockout — SPEC-PULSE-03.

Uses the BigQuery ML ARIMA_PLUS forecast adapter (canned in mock mode) to
predict the next stockout. Only surfaces predictions with confidence >= 0.70.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.bigquery_client import get_bigquery
from tools.shared.errors import error
from tools.shared.logger import get_logger

logger = get_logger("pulse.predict_stockout")
router = APIRouter()

_MIN_CONFIDENCE = 0.70


def predict_stockout(product_id: str, store_id: str, forecast_days: int = 7) -> dict:
    """
    Uses BigQuery ML ARIMA_PLUS to forecast the next stockout for a product.
    Only surfaces predictions with confidence >= 0.70. Returns predicted_date,
    confidence, days_until_stockout, and evidence.
    """
    if forecast_days <= 0:
        return error("VALIDATION_ERROR", "forecast_days must be > 0")

    bq = get_bigquery()
    fc = bq.forecast_stockout(product_id=product_id, store_id=store_id, forecast_days=forecast_days)

    if fc["confidence"] < _MIN_CONFIDENCE:
        return {
            "surfaced": False,
            "reason": f"confidence {fc['confidence']:.2f} below 0.70 threshold",
            "confidence": fc["confidence"],
        }

    result = {
        "surfaced": True,
        "predicted_stockout_date": fc["predicted_stockout_date"],
        "days_until_stockout": fc["days_until_stockout"],
        "confidence": fc["confidence"],
        "current_stock": fc["current_stock"],
        "daily_consumption_rate": fc["daily_consumption_rate"],
        "evidence": fc["evidence"],
    }
    logger.info(
        "predict_stockout",
        tool="predict_stockout",
        product_id=product_id,
        confidence=fc["confidence"],
        status="success",
    )
    return result


class PredictStockoutRequest(BaseModel):
    product_id: str
    store_id: str
    forecast_days: int = 7


@router.post("/tools/predict-stockout")
async def predict_stockout_endpoint(req: PredictStockoutRequest) -> dict:
    return predict_stockout(req.product_id, req.store_id, req.forecast_days)
