"""FastAPI app for ARIA tool functions — SPEC-00 §7.

Serves the 9 ARIA tools as HTTP endpoints on Cloud Run. Each tool module
exposes an APIRouter that is included here behind IAM auth. Routers are added
as the tools are implemented (SPEC-ARIA-01..09).
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from slowapi.errors import RateLimitExceeded

from tools.shared.auth import verify_iam_token
from tools.shared.logger import get_logger
from tools.shared.rate_limit import handle_rate_limit, limiter

logger = get_logger("aria_tools")

app = FastAPI(
    title="ARC ARIA Tool Functions",
    version="1.0.0",
    description="ARIA agent tool functions for MIRA Retail",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, handle_rate_limit)

# ── Tool routers (each guarded by IAM auth) ──────────────────────────
from tools.aria_tools import (  # noqa: E402
    apply_promotion,
    build_cart,
    check_stock,
    get_customer_context,
    log_session,
    optimize_budget,
    parse_intent,
    place_order,
    suggest_substitution,
)

_AUTH = [Depends(verify_iam_token)]
app.include_router(parse_intent.router, dependencies=_AUTH)
app.include_router(get_customer_context.router, dependencies=_AUTH)
app.include_router(build_cart.router, dependencies=_AUTH)
app.include_router(check_stock.router, dependencies=_AUTH)
app.include_router(suggest_substitution.router, dependencies=_AUTH)
app.include_router(optimize_budget.router, dependencies=_AUTH)
app.include_router(apply_promotion.router, dependencies=_AUTH)
app.include_router(place_order.router, dependencies=_AUTH)
app.include_router(log_session.router, dependencies=_AUTH)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "arc-aria-tools"}
