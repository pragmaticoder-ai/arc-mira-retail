"""Retry helper (tenacity) for DB/BQ/LLM calls — SPEC §9 NFRs.

Each spec defines retry policy (e.g. "retry up to 3 times with exponential
backoff" on DB timeout). This wraps a callable with that policy. In mock mode
calls don't fail, so retries are inert; the wrapper exists so the real adapter
calls inherit the policy without touching tool code.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from tenacity import retry, stop_after_attempt, wait_exponential

T = TypeVar("T")


def with_retry(attempts: int = 3, *, min_wait: float = 1.0, max_wait: float = 10.0):
    """Decorator: retry on any exception with exponential backoff."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        return retry(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            reraise=True,
        )(fn)

    return decorator
