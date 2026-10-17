"""Vector search adapter (AlloyDB AI / ScaNN) — real TF-IDF cosine in mock.

suggest_substitution() uses this to find semantically similar in-stock products.
The mock computes cosine similarity over the TF-IDF product space from
embeddings.py, so results are genuinely semantic (rice→rice/grains). Real impl
(TODO) runs the ScaNN SQL query in ARCHITECTURE.md §6.

Caller passes max_price_aed; SPEC-ARIA-05 also wants substitutes within ~20% of
the original price, which suggest_substitution enforces via max_price_aed.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

from tools.shared.embeddings import get_embeddings, product_document
from tools.shared.settings import settings


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class VectorSearch(ABC):
    @abstractmethod
    def nearest_in_stock(
        self,
        *,
        query_text: str,
        store_id: str,
        dietary_preference: str,
        max_price_aed: float,
        min_price_aed: float = 0.0,
        exclude_product_id: str | None = None,
        limit: int = 1,
    ) -> list[dict]:
        """Return nearest in-stock products as
        [{product_id, product_name, price_aed, similarity_score}]."""


class MockVectorSearch(VectorSearch):
    """In-process TF-IDF cosine search over the shared mock inventory."""

    def nearest_in_stock(
        self,
        *,
        query_text: str,
        store_id: str,
        dietary_preference: str,
        max_price_aed: float,
        min_price_aed: float = 0.0,
        exclude_product_id: str | None = None,
        limit: int = 1,
    ) -> list[dict]:
        from tools.shared.mock_inventory import MOCK_INVENTORY

        emb = get_embeddings()
        q = emb.embed(query_text)

        candidates: list[dict] = []
        for p in MOCK_INVENTORY:
            if p["store_id"] != store_id:
                continue
            if p["product_id"] == exclude_product_id:
                continue
            if p["stock_quantity"] <= 0:
                continue
            if max_price_aed and p["price_aed"] > max_price_aed:
                continue
            if p["price_aed"] < min_price_aed:
                continue
            if dietary_preference and dietary_preference != "none":
                if dietary_preference not in p["dietary_flags"]:
                    continue
            sim = _cosine(q, emb.embed(product_document(p)))
            candidates.append(
                {
                    "product_id": p["product_id"],
                    "product_name": p["product_name"],
                    "price_aed": p["price_aed"],
                    "category": p["category"],
                    "similarity_score": round(sim, 4),
                }
            )

        candidates.sort(key=lambda c: c["similarity_score"], reverse=True)
        return candidates[:limit]


class RealVectorSearch(VectorSearch):
    """TODO(backend): ScaNN cosine query from ARCHITECTURE.md §6 against AlloyDB
    (embedding <=> query_embedding), same dietary/price/stock filters."""

    def nearest_in_stock(self, **kwargs) -> list[dict]:
        raise NotImplementedError(
            "RealVectorSearch not implemented. Set USE_MOCK=true or wire AlloyDB ScaNN."
        )


def get_vector_search() -> VectorSearch:
    return MockVectorSearch() if settings.use_mock else RealVectorSearch()
