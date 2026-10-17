"""Vector search adapter (AlloyDB AI / ScaNN) — placeholder with mock impl.

suggest_substitution() uses this to find semantically similar in-stock products.
Tools depend on this interface, not on the AlloyDB ScaNN SQL directly.

Mock computes cosine similarity in Python against the seed inventory using the
MockEmbeddings vectors, filtered by dietary + price + stock, mirroring the real
ScaNN query in ARCHITECTURE.md §6. Real impl (TODO) runs the SQL ScaNN query.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

from tools.shared.embeddings import get_embeddings
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
        exclude_product_id: str | None = None,
        limit: int = 1,
    ) -> list[dict]:
        """Return nearest in-stock products as
        [{product_id, product_name, price_aed, similarity_score}]."""


class MockVectorSearch(VectorSearch):
    """In-process cosine search over the shared mock inventory."""

    def nearest_in_stock(
        self,
        *,
        query_text: str,
        store_id: str,
        dietary_preference: str,
        max_price_aed: float,
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
            if dietary_preference and dietary_preference != "none":
                if dietary_preference not in p["dietary_flags"]:
                    continue
            sim = _cosine(q, emb.embed(f"{p['product_name']} {p['category']} {p['dietary_flags']}"))
            candidates.append(
                {
                    "product_id": p["product_id"],
                    "product_name": p["product_name"],
                    "price_aed": p["price_aed"],
                    "similarity_score": round(sim, 4),
                }
            )

        candidates.sort(key=lambda c: c["similarity_score"], reverse=True)
        return candidates[:limit]


class RealVectorSearch(VectorSearch):
    """TODO(backend): implement the ScaNN cosine query from ARCHITECTURE.md §6
    against AlloyDB (embedding <=> query_embedding)."""

    def nearest_in_stock(self, **kwargs) -> list[dict]:
        raise NotImplementedError(
            "RealVectorSearch not implemented. Set USE_MOCK=true or wire AlloyDB ScaNN."
        )


def get_vector_search() -> VectorSearch:
    return MockVectorSearch() if settings.use_mock else RealVectorSearch()
