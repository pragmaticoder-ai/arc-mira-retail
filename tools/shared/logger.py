"""Structured logging with structlog.

All ARC tools log in JSON format with consistent fields:
- agent: "ARIA" or "PULSE"
- tool: function name
- latency_ms: execution time
- status: "success" or "error"
"""

from __future__ import annotations

import structlog
from tools.shared.settings import settings


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured structlog logger."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.JSONRenderer()
            if settings.environment == "production"
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlib.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger(name)
