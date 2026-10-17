"""Rate limiting (slowapi) — SPEC-00 §8.

Shared limiter keyed by client IP. Per-endpoint limits are applied as
decorators in each tool router (see SPEC-00 §8 reference table).
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from tools.shared.settings import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)
