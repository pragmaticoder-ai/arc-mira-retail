"""PULSE tool: detect_patterns

Queries BigQuery incidents table to detect stockout patterns.
This is the first tool PULSE calls - the foundation of all OPS intelligence.

Spec: specs/SPEC-PULSE-01-detect_patterns.md
"""

from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from tools.shared.models import (
    DetectPatternsRequest,
    DetectPatternsResponse,
    StockoutPattern,
    PatternEvidence,
)
from tools.shared.logger import get_logger
from tools.shared.settings import settings

router = APIRouter()
logger = get_logger(__name__)


@router.post("/detect-patterns", response_model=DetectPatternsResponse)
async def detect_patterns(request: DetectPatternsRequest):
    """
    Detect stockout patterns from BigQuery incidents table.
    
    Returns:
        DetectPatternsResponse: list of patterns ranked by revenue impact
    """
    try:
        # Mock implementation for local development
        if settings.use_mock:
            # Simulate brown rice stockout pattern (the demo scenario)
            patterns = []
            
            # Create a realistic pattern for brown rice at Dubai Marina
            if request.store_id == "dubai_marina_01":
                # Calculate estimated revenue impact
                incident_count = 23
                avg_cart = 40.0
                margin_pct = 0.15
                estimated_revenue_lost = incident_count * avg_cart * margin_pct
                
                pattern = StockoutPattern(
                    product_id="rice_brown_500g",
                    product_name="Brown Rice 500g",
                    store_id=request.store_id,
                    incident_count=incident_count,
                    period_hours=request.hours,
                    estimated_revenue_lost_aed=round(estimated_revenue_lost, 2),
                    peak_hour="10:00-12:00",
                    abandonment_count=5,
                    evidence=PatternEvidence(
                        first_incident=(datetime.now() - timedelta(hours=request.hours)).isoformat(),
                        last_incident=datetime.now().isoformat(),
                        sample_session_ids=[
                            "550e8400-e29b-41d4-a716-446655440000",
                            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                            "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                        ],
                        substitution_acceptance_rate=0.78,
                    ),
                )
                patterns.append(pattern)
            
            logger.info(
                "detect_patterns_mock_success",
                store_id=request.store_id,
                patterns_found=len(patterns),
                hours=request.hours,
            )
            
            return DetectPatternsResponse(patterns=patterns)
        
        # Production: query BigQuery
        # TODO: Implement real BigQuery query
        from google.cloud import bigquery
        
        client = bigquery.Client(project=settings.google_cloud_project)
        
        query = f"""
        SELECT
            product_id,
            COUNT(*) as incident_count,
            SUM(cart_total_aed * 0.15) as estimated_revenue_lost,
            MIN(timestamp) as first_seen,
            MAX(timestamp) as last_seen,
            COUNTIF(order_placed = false) as abandonment_count
        FROM `{settings.google_cloud_project}.{settings.bigquery_dataset}.incidents`,
        UNNEST(items_unavailable) as unavailable_item
        WHERE store_id = @store_id
        AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @hours HOUR)
        GROUP BY product_id
        HAVING incident_count >= @min_incidents
        ORDER BY estimated_revenue_lost DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("store_id", "STRING", request.store_id),
                bigquery.ScalarQueryParameter("hours", "INT64", request.hours),
                bigquery.ScalarQueryParameter("min_incidents", "INT64", request.min_incidents),
            ]
        )
        
        results = client.query(query, job_config=job_config).result()
        
        patterns = []
        for row in results:
            patterns.append(StockoutPattern(
                product_id=row.product_id,
                product_name="",  # TODO: join with inventory
                store_id=request.store_id,
                incident_count=row.incident_count,
                period_hours=request.hours,
                estimated_revenue_lost_aed=round(row.estimated_revenue_lost, 2),
                peak_hour="",  # TODO: calculate from incident timestamps
                abandonment_count=row.abandonment_count,
                evidence=PatternEvidence(
                    first_incident=row.first_seen.isoformat(),
                    last_incident=row.last_seen.isoformat(),
                    sample_session_ids=[],
                    substitution_acceptance_rate=0.0,
                ),
            ))
        
        logger.info(
            "detect_patterns_success",
            store_id=request.store_id,
            patterns_found=len(patterns),
        )
        
        return DetectPatternsResponse(patterns=patterns)
        
    except Exception as e:
        logger.error("detect_patterns_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
