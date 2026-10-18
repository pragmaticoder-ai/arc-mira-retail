"""Rate limiting (slowapi) — SPEC-00 §8.

Shared limiter keyed by client IP. Per-endpoint limits are applied as
decorators in each tool router (see SPEC-00 §8 reference table).
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from tools.shared.settings import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)


def handle_rate_limit(request: Request, exc: Exception) -> Response:
    """Adapt SlowAPI's narrower handler signature to Starlette's interface."""
    if not isinstance(exc, RateLimitExceeded):
        raise exc
    return _rate_limit_exceeded_handler(request, exc)
