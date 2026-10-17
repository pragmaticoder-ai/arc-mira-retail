"""Structured logging (structlog) for ARC tools — SPEC-00 §8.

JSON logs so Cloud Logging ingests them cleanly. Every tool call logs
agent/tool/latency/status (ARC_SPEC §7.5 observability).
"""

from __future__ import annotations

import structlog

from tools.shared.settings import settings

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
    _configured = True


def get_logger(name: str) -> structlog.BoundLogger:
    _configure()
    return structlog.get_logger(name).bind(environment=settings.environment)
