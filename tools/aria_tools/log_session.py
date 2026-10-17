"""ARIA tool: log_session

Writes the complete session summary to BigQuery incidents table.
This is the bridge between ARIA and PULSE.

Spec: specs/SPEC-ARIA-09-log_session.md
"""

from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, HTTPException
from tools.shared.models import LogSessionRequest, LogSessionResponse
from tools.shared.logger import get_logger
from tools.shared.settings import settings

router = APIRouter()
logger = get_logger(__name__)


@router.post("/log-session", response_model=LogSessionResponse)
async def log_session(request: LogSessionRequest):
    """
    Write session summary to BigQuery incidents table.
    
    CRITICAL: This is the bridge that enables PULSE intelligence.
    ALWAYS call this as the absolute last step of every session.
    
    Returns:
        LogSessionResponse: session_id, logged status, timestamp
    """
    try:
        # In mock mode, just log to console
        if settings.use_mock:
            logger.info(
                "log_session_mock",
                session_id=request.session_id,
                customer_id=request.customer_id,
                store_id=request.store_id,
                order_placed=request.order_placed,
                items_unavailable=len(request.items_unavailable),
            )
            
            return LogSessionResponse(
                session_id=request.session_id,
                logged=True,
                timestamp=datetime.now().isoformat(),
            )
        
        # Production: write to BigQuery
        # TODO: Implement real BigQuery streaming insert
        from google.cloud import bigquery
        
        client = bigquery.Client(project=settings.google_cloud_project)
        table_id = f"{settings.google_cloud_project}.{settings.bigquery_dataset}.incidents"
        
        row = {
            "session_id": request.session_id,
            "customer_id": request.customer_id,
            "store_id": request.store_id,
            "timestamp": datetime.now().isoformat(),
            "items_ordered": request.items_ordered,
            "items_unavailable": request.items_unavailable,
            "substitutions_offered": request.substitutions,
            "promotion_id": request.promotion_id,
            "promotion_saving_aed": request.promotion_saving_aed,
            "cart_total_aed": request.cart_total_aed,
            "budget_aed": request.budget_aed,
            "session_sentiment": request.sentiment,
            "order_placed": request.order_placed,
            "abandonment_reason": request.abandonment_reason,
        }
        
        errors = client.insert_rows_json(table_id, [row])
        
        if errors:
            logger.error("log_session_bigquery_error", errors=errors)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to log session: {errors}"
            )
        
        logger.info(
            "log_session_success",
            session_id=request.session_id,
            logged=True,
        )
        
        return LogSessionResponse(
            session_id=request.session_id,
            logged=True,
            timestamp=datetime.now().isoformat(),
        )
        
    except Exception as e:
        logger.error("log_session_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
