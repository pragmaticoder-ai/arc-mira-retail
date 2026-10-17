"""ARIA Tools FastAPI Application

Main FastAPI app that wires all 9 ARIA tool functions:
1. parse_intent
2. get_customer_context
3. build_cart
4. check_stock
5. suggest_substitution
6. optimize_budget
7. apply_promotion
8. place_order
9. log_session
"""

from __future__ import annotations

from fastapi import FastAPI, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from tools.shared.auth import verify_iam_token
from tools.shared.logger import get_logger

# Import all tool routers
from tools.aria_tools.parse_intent import router as parse_intent_router
from tools.aria_tools.get_customer_context import router as get_customer_context_router
from tools.aria_tools.build_cart import router as build_cart_router
from tools.aria_tools.check_stock import router as check_stock_router
from tools.aria_tools.suggest_substitution import router as suggest_substitution_router
from tools.aria_tools.optimize_budget import router as optimize_budget_router
from tools.aria_tools.apply_promotion import router as apply_promotion_router
from tools.aria_tools.place_order import router as place_order_router
from tools.aria_tools.log_session import router as log_session_router

logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="ARC ARIA Tool Functions",
    version="1.0.0",
    description="ARIA agent tool functions for MIRA Retail CX agent",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "arc-aria-tools"}


# Register all tool routers with auth
app.include_router(
    parse_intent_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    get_customer_context_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    build_cart_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    check_stock_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    suggest_substitution_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    optimize_budget_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    apply_promotion_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    place_order_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)
app.include_router(
    log_session_router,
    prefix="/tools",
    dependencies=[Depends(verify_iam_token)]
)


@app.on_event("startup")
async def startup_event():
    """Log startup."""
    logger.info("aria_tools_startup", message="ARIA Tools API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown."""
    logger.info("aria_tools_shutdown", message="ARIA Tools API stopped")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
