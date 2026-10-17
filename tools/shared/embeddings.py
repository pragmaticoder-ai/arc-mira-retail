"""Embeddings adapter (textembedding-gecko) — placeholder with mock impl.

Used to embed product text for AlloyDB AI vector search. Tools never call the
embedding SDK directly; they go through this interface.

Mock returns a deterministic pseudo-embedding derived from the input hash, so
similarity ordering is stable and reproducible offline. Real implementation
(TODO) calls Vertex AI text embeddings.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

import httpx

from tools.shared.settings import settings


class Embeddings(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return an embedding_dim-length vector for the text."""


class MockEmbeddings(Embeddings):
    def embed(self, text: str) -> list[float]:
        if settings.mock_server_url:
            resp = httpx.post(
                f"{settings.mock_server_url}/v1/embeddings",
                json={"text": text, "model": settings.embedding_model},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()["embedding"]
        return self._deterministic(text)

    @staticmethod
    def _deterministic(text: str) -> list[float]:
        dim = settings.embedding_dim
        digest = hashlib.sha256(text.lower().encode()).digest()
        # Expand the 32-byte digest into a dim-length vector in [-1, 1].
        vals = [((digest[i % len(digest)] / 255.0) * 2.0) - 1.0 for i in range(dim)]
        return vals


class RealEmbeddings(Embeddings):
    """TODO(backend): implement with vertexai.language_models
    TextEmbeddingModel.from_pretrained(settings.embedding_model)."""

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError(
            "RealEmbeddings.embed not implemented. Set USE_MOCK=true or wire Vertex AI."
        )


def get_embeddings() -> Embeddings:
    return MockEmbeddings() if settings.use_mock else RealEmbeddings()
