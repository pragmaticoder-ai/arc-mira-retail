"""FastAPI app for PULSE tool functions — SPEC-00 §7.

Serves the 6 PULSE tools as HTTP endpoints on Cloud Run. Routers are added as
the tools are implemented (SPEC-PULSE-01..06).
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from tools.shared.auth import verify_iam_token
from tools.shared.logger import get_logger
from tools.shared.rate_limit import limiter

logger = get_logger("pulse_tools")

app = FastAPI(
    title="ARC PULSE Tool Functions",
    version="1.0.0",
    description="PULSE agent tool functions for MIRA Retail",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Tool routers (each guarded by IAM auth) ──────────────────────────
from tools.pulse_tools import (  # noqa: E402
    calculate_impact,
    detect_patterns,
    draft_purchase_order,
    execute_perishable_discount,
    find_root_cause,
    predict_stockout,
)

_AUTH = [Depends(verify_iam_token)]
app.include_router(detect_patterns.router, dependencies=_AUTH)
app.include_router(find_root_cause.router, dependencies=_AUTH)
app.include_router(predict_stockout.router, dependencies=_AUTH)
app.include_router(calculate_impact.router, dependencies=_AUTH)
app.include_router(draft_purchase_order.router, dependencies=_AUTH)
app.include_router(execute_perishable_discount.router, dependencies=_AUTH)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "arc-pulse-tools"}
