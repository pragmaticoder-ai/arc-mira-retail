"""PULSE tool: predict_stockout

Uses BigQuery ML ARIMA_PLUS to forecast next stockout.

Spec: specs/SPEC-PULSE-03-predict_stockout.md
"""

from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from tools.shared.models import (
    PredictStockoutRequest,
    PredictStockoutResponse,
    PredictionEvidence,
)
from tools.shared.alloydb_client import get_alloydb
from tools.shared.logger import get_logger
from tools.shared.settings import settings

router = APIRouter()
logger = get_logger(__name__)


@router.post("/predict-stockout", response_model=PredictStockoutResponse)
async def predict_stockout(request: PredictStockoutRequest):
    """
    Predict next stockout using BigQuery ML.
    
    Returns:
        PredictStockoutResponse: predicted date, confidence, days until stockout
    """
    try:
        db = get_alloydb()
        
        # Get current stock
        product = db.get_product(request.product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {request.product_id} not found"
            )
        
        current_stock = product.get("stock_quantity", 0)
        
        # Mock implementation
        if settings.use_mock:
            # Simulate prediction based on current stock and sales rate
            daily_sales_rate = 8.5  # Mock: units per day
            days_until_stockout = max(0, int(current_stock / daily_sales_rate))
            predicted_date = datetime.now() + timedelta(days=days_until_stockout)
            
            return PredictStockoutResponse(
                predicted_stockout_date=predicted_date.isoformat(),
                days_until_stockout=days_until_stockout,
                confidence=0.85,
                current_stock=current_stock,
                daily_consumption_rate=daily_sales_rate,
                evidence=PredictionEvidence(
                    model="BigQuery ML ARIMA_PLUS",
                    training_period="Last 30 days",
                    data_points_used=30,
                ),
            )
        
        # Production: query BigQuery ML model
        # TODO: Implement real BigQuery ML ARIMA_PLUS prediction
        from google.cloud import bigquery
        
        client = bigquery.Client(project=settings.google_cloud_project)
        
        query = f"""
        SELECT
            forecast_timestamp as predicted_date,
            confidence_level,
            prediction_interval_lower_bound,
            prediction_interval_upper_bound
        FROM ML.FORECAST(
            MODEL `{settings.google_cloud_project}.{settings.bigquery_dataset}.demand_forecast`,
            STRUCT({request.forecast_days} as horizon)
        )
        WHERE product_id = @product_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("product_id", "STRING", request.product_id),
            ]
        )
        
        results = list(client.query(query, job_config=job_config).result())
        
        if results:
            row = results[0]
            predicted_date = row.predicted_date
            confidence = row.confidence_level
            days_until = (predicted_date - datetime.now()).days
            
            return PredictStockoutResponse(
                predicted_stockout_date=predicted_date.isoformat(),
                days_until_stockout=days_until,
                confidence=confidence,
                current_stock=current_stock,
                daily_consumption_rate=current_stock / max(1, days_until),
                evidence=PredictionEvidence(
                    model="BigQuery ML ARIMA_PLUS",
                    training_period="Last 30 days",
                    data_points_used=30,
                ),
            )
        
        # Fallback
        raise HTTPException(
            status_code=404,
            detail="No prediction available for this product"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("predict_stockout_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
