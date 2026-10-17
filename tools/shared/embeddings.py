"""Embeddings adapter — real TF-IDF semantic vectors (pure Python, no deps).

In production this is replaced by Vertex AI textembedding-gecko (RealEmbeddings,
TODO). The mock computes a genuine TF-IDF vector over a fixed product-text
vocabulary so cosine similarity is semantically meaningful: "brown rice" lands
near other rice/grain products, not unrelated items. Deterministic and offline.

The vocabulary + IDF are derived from the shared product corpus once, so every
embed() call projects into the same space (required for meaningful cosine).
"""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod

import httpx

from tools.shared.retry import with_retry
from tools.shared.settings import settings

_TOKEN = re.compile(r"[a-z0-9]+")


def product_document(p: dict) -> str:
    """Canonical text for a product. The name is weighted (repeated) because
    it carries the most discriminative signal (e.g. 'rice'), and the category
    is included so same-category items cluster. Shared by the corpus builder
    and callers so query/doc vectors live in the same space."""
    name = p["product_name"]
    return f"{name} {name} {p['category']} {p['category']} {p.get('brand', '')} {p['dietary_flags']}"


def _tokenize(text: str) -> list[str]:
    # Lowercase word tokens; split size tokens like "500g" into "500" + "g".
    raw = _TOKEN.findall(text.lower())
    out: list[str] = []
    for t in raw:
        m = re.match(r"^(\d+)([a-z]+)$", t)
        if m:
            out.extend([m.group(1), m.group(2)])
        else:
            out.append(t)
    return out


class _TfidfSpace:
    """Fixed TF-IDF vector space built from the product corpus (built once)."""

    def __init__(self) -> None:
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self._built = False

    def _corpus(self) -> list[str]:
        from tools.shared.mock_inventory import MOCK_INVENTORY

        return [product_document(p) for p in MOCK_INVENTORY]

    def build(self) -> None:
        if self._built:
            return
        docs = self._corpus()
        df: dict[str, int] = {}
        for doc in docs:
            for tok in set(_tokenize(doc)):
                df[tok] = df.get(tok, 0) + 1
        n = max(1, len(docs))
        self.vocab = {tok: i for i, tok in enumerate(sorted(df))}
        self.idf = {tok: math.log((1 + n) / (1 + c)) + 1.0 for tok, c in df.items()}
        self._built = True

    def vectorize(self, text: str) -> list[float]:
        self.build()
        vec = [0.0] * len(self.vocab)
        toks = _tokenize(text)
        if not toks:
            return vec
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        for tok, count in tf.items():
            idx = self.vocab.get(tok)
            if idx is None:
                continue  # out-of-vocabulary token (unseen in corpus)
            vec[idx] = (count / len(toks)) * self.idf.get(tok, 0.0)
        return vec


_SPACE = _TfidfSpace()


class Embeddings(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return a TF-IDF vector for the text in the shared product space."""


class MockEmbeddings(Embeddings):
    def embed(self, text: str) -> list[float]:
        if settings.mock_server_url:
            return self._embed_http(text)
        return _SPACE.vectorize(text)

    @with_retry(attempts=3)
    def _embed_http(self, text: str) -> list[float]:
        resp = httpx.post(
            f"{settings.mock_server_url}/v1/embeddings",
            json={"text": text, "model": settings.embedding_model},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


class RealEmbeddings(Embeddings):
    """TODO(backend): vertexai.language_models.TextEmbeddingModel
    .from_pretrained(settings.embedding_model).get_embeddings([text])."""

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError(
            "RealEmbeddings.embed not implemented. Set USE_MOCK=true or wire Vertex AI."
        )


def get_embeddings() -> Embeddings:
    return MockEmbeddings() if settings.use_mock else RealEmbeddings()
