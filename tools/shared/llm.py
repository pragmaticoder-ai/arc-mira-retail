"""LLM adapter (Gemini via Vertex AI) — placeholder with mock implementation.

The agent reasons through tool docstrings; a few tools also need direct LLM
calls (build_cart goal->categories mapping, optimize_budget reasoning). Those
tools depend on this interface, never on the Vertex AI SDK directly, so the
mock swaps to real with one env flag.

Real implementation (TODO for backend engineer): wire vertexai.generative_models
GenerativeModel in RealLLM.generate(). Mock returns deterministic canned output
so flows are demo-stable and offline.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx

from tools.shared.settings import settings

# Grocery categories the agent is allowed to use (ARC_SPEC FR-ARIA-03).
ALLOWED_CATEGORIES = [
    "dairy",
    "grains",
    "halal_meat",
    "vegetables",
    "fruits",
    "beverages",
    "snacks",
    "condiments",
]


class LLM(ABC):
    """Abstract LLM interface. Tools depend on this, not on any SDK."""

    @abstractmethod
    def generate(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> str:
        """Return a plain-text completion for the prompt."""

    @abstractmethod
    def classify_goal_to_categories(self, goal: str) -> list[str]:
        """Map a shopping goal to a subset of ALLOWED_CATEGORIES."""


class MockLLM(LLM):
    """Deterministic mock. Runs in-process, or routes to the mock server
    when MOCK_SERVER_URL is set (to simulate a real API call)."""

    def generate(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> str:
        if settings.mock_server_url:
            resp = httpx.post(
                f"{settings.mock_server_url}/v1/gemini/generate",
                json={"prompt": prompt, "model": model or settings.gemini_flash_model},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()["text"]
        return self._canned(prompt)

    def classify_goal_to_categories(self, goal: str) -> list[str]:
        g = goal.lower()
        if "biryani" in g:
            return ["grains", "halal_meat", "condiments", "vegetables"]
        if "breakfast" in g:
            return ["dairy", "grains", "fruits", "beverages"]
        if "snack" in g or "party" in g:
            return ["snacks", "beverages", "fruits"]
        # "weekly groceries" and general goals -> a broad everyday basket
        return ["dairy", "grains", "halal_meat", "vegetables", "fruits", "beverages"]

    @staticmethod
    def _canned(prompt: str) -> str:
        # Minimal structured echo so callers that expect JSON still parse.
        return json.dumps({"mock": True, "prompt_preview": prompt[:120]})


class RealLLM(LLM):
    """TODO(backend): implement with vertexai.generative_models.GenerativeModel.
    Kept as an explicit placeholder so the wiring point is obvious."""

    def generate(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> str:
        raise NotImplementedError(
            "RealLLM.generate not implemented. Set USE_MOCK=true or wire Vertex AI."
        )

    def classify_goal_to_categories(self, goal: str) -> list[str]:
        raise NotImplementedError(
            "RealLLM.classify_goal_to_categories not implemented. Set USE_MOCK=true "
            "or wire a Gemini Flash call."
        )


def get_llm() -> LLM:
    """Factory — returns the mock or real LLM based on settings.use_mock."""
    return MockLLM() if settings.use_mock else RealLLM()
