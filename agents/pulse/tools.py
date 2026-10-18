"""PULSE tool bindings for Google ADK.

Wraps the 6 PULSE tool functions as ADK FunctionTools.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from google.adk.tools import FunctionTool

from tools.pulse_tools.calculate_impact import calculate_impact
from tools.pulse_tools.detect_patterns import detect_patterns
from tools.pulse_tools.draft_purchase_order import draft_purchase_order
from tools.pulse_tools.execute_perishable_discount import execute_perishable_discount
from tools.pulse_tools.find_root_cause import find_root_cause
from tools.pulse_tools.predict_stockout import predict_stockout

PULSE_FUNCTIONS: list[Callable[..., Any]] = [
    detect_patterns,
    find_root_cause,
    predict_stockout,
    calculate_impact,
    draft_purchase_order,
    execute_perishable_discount,
]

PULSE_TOOLS = [FunctionTool(fn) for fn in PULSE_FUNCTIONS]
