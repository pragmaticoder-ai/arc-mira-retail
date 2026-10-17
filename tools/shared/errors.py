"""Shared error helpers for tool functions.

Every tool returns a plain dict. On failure it returns the standard error
shape from AGENT_CONTRACTS.md. These helpers keep that consistent.
"""

from __future__ import annotations


def error(code: str, message: str, retry: bool = False) -> dict:
    return {
        "error": True,
        "error_code": code,
        "error_message": message,
        "retry_suggested": retry,
    }


def is_error(result: dict) -> bool:
    return bool(result.get("error"))
