"""PULSE agent definition (Google ADK).

Builds the ADK Agent from the existing PULSE system prompt and the 6 bound
tools. Constructed only when a real LLM is configured; mock mode uses the
deterministic cycle in main.py.
"""

from __future__ import annotations

from pathlib import Path

from tools.shared.settings import settings

_PROMPT_PATH = Path(__file__).parent / "system_prompt.txt"


def load_system_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def build_agent():
    from google.adk.agents import Agent

    from agents.pulse.tools import PULSE_TOOLS

    return Agent(
        name="pulse",
        model=settings.gemini_pro_model,
        instruction=load_system_prompt(),
        tools=PULSE_TOOLS,
    )


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent
