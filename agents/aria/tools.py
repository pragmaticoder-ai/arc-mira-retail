"""ARIA tool bindings for Google ADK.

Wraps the 9 ARIA tool functions as ADK FunctionTools. The ADK agent reasons
through each function's docstring (the docstrings are the reasoning
instructions — ARCHITECTURE.md §2).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from google.adk.tools import FunctionTool

from tools.aria_tools.apply_promotion import apply_promotion
from tools.aria_tools.build_cart import build_cart
from tools.aria_tools.check_stock import check_stock
from tools.aria_tools.get_customer_context import get_customer_context
from tools.aria_tools.log_session import log_session
from tools.aria_tools.optimize_budget import optimize_budget
from tools.aria_tools.parse_intent import parse_intent
from tools.aria_tools.place_order import place_order
from tools.aria_tools.suggest_substitution import suggest_substitution

ARIA_FUNCTIONS: list[Callable[..., Any]] = [
    parse_intent,
    get_customer_context,
    build_cart,
    check_stock,
    suggest_substitution,
    optimize_budget,
    apply_promotion,
    place_order,
    log_session,
]

ARIA_TOOLS = [FunctionTool(fn) for fn in ARIA_FUNCTIONS]
