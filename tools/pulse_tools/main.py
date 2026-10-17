"""PULSE Tools FastAPI Application

Main FastAPI app that wires all 6 PULSE tool functions:
1. detect_patterns
2. find_root_cause
3. predict_stockout
4. calculate_impact
5. draft_purchase_order
6. execute_perishable_discount
"""

from __future__ import annotations

from fastapi import FastAPI, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from tools.shared.auth import verify_iam_token
from tools.shared.logger import get_logger

# Import all tool routers
from tools.pulse_tools.detect_patterns import router as detect_patterns_router
from tools.pulse_tools.find_root_cause import router as find_root_cause_router
from tools.pulse_tools.predict_stockout import router as predict_stockout_router
from tools.pulse_tools.calculate_impact import router as calculate_impact_router
from tools.pulse_tools.draft_purchase_order import router as draft_purchase_order_router
from tools.pulse_tools.execute_perishable_discount import router as execute_perishable_discount_router

logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="ARC PULSE Tool Functions",
    version="1.0.0",
    description="PULSE agent tool functions for MIRA Retail OPS agent",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "arc-pulse-tools"}


# Register all tool routers with auth
app.include_router(
    detect_patterns_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    find_root_cause_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    predict_stockout_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    calculate_impact_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    draft_purchase_order_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    execute_perishable_discount_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)


@app.on_event("startup")
async def startup_event():
    """Log startup."""
    logger.info("pulse_tools_startup", message="PULSE Tools API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown."""
    logger.info("pulse_tools_shutdown", message="PULSE Tools API stopped")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
