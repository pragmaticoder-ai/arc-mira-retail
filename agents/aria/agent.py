"""ARIA agent definition (Google ADK).

Builds the ADK Agent from the existing system prompt and the 9 bound tools.
The agent is constructed only when a real LLM is configured (USE_MOCK=false);
in mock mode the HTTP layer uses a deterministic orchestration instead so the
demo runs offline (see main.py).
"""

from __future__ import annotations

from pathlib import Path

from tools.shared.settings import settings

_PROMPT_PATH = Path(__file__).parent / "system_prompt.txt"


def load_system_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def build_agent():
    """Construct the ADK Agent. Requires a configured Gemini model.

    Returns the google.adk Agent instance. Raises if ADK/model unavailable.
    """
    from google.adk.agents import Agent

    from agents.aria.tools import ARIA_TOOLS

    return Agent(
        name="aria",
        model=settings.gemini_pro_model,
        instruction=load_system_prompt(),
        tools=ARIA_TOOLS,
    )


# Lazily built so importing this module never requires GCP credentials.
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent
