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

from tools.shared.retry import with_retry
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
            return self._generate_http(prompt, model)
        return self._canned(prompt)

    @with_retry(attempts=3)
    def _generate_http(self, prompt: str, model: str | None) -> str:
        resp = httpx.post(
            f"{settings.mock_server_url}/v1/gemini/generate",
            json={"prompt": prompt, "model": model or settings.gemini_flash_model},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["text"]

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
    """Production Vertex AI Gemini adapter."""

    def __init__(self) -> None:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=settings.google_cloud_project, location=settings.vertex_ai_location)
        self._flash_model = GenerativeModel(settings.gemini_flash_model)
        self._pro_model = GenerativeModel(settings.gemini_pro_model)

    def generate(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> str:
        selected_model = self._pro_model if model and "pro" in model else self._flash_model
        response = selected_model.generate_content(prompt, **kwargs)
        return response.text

    def classify_goal_to_categories(self, goal: str) -> list[str]:
        prompt = (
            f"You are a retail grocery categorizer. Given the customer shopping goal: '{goal}', "
            f"select only the relevant categories from this allowed list: {ALLOWED_CATEGORIES}. "
            "Return a valid JSON array of category strings, e.g. [\"dairy\", \"grains\"]. Do not include markdown or explanations."
        )
        try:
            raw = self.generate(prompt)
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            parsed = json.loads(clean.strip())
            if isinstance(parsed, list):
                valid = [c for c in parsed if c in ALLOWED_CATEGORIES]
                if valid:
                    return valid
        except Exception:
            pass

        # Fallback to rule matching if offline or parsing error
        g = goal.lower()
        if "biryani" in g:
            return ["grains", "halal_meat", "condiments", "vegetables"]
        if "breakfast" in g:
            return ["dairy", "grains", "fruits", "beverages"]
        if "snack" in g or "party" in g:
            return ["snacks", "beverages", "fruits"]
        return ["dairy", "grains", "halal_meat", "vegetables", "fruits", "beverages"]


def get_llm() -> LLM:
    """Factory — returns the mock or real LLM based on settings.use_mock."""
    return MockLLM() if settings.use_mock else RealLLM()
