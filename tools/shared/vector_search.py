"""PostgreSQL pgvector search; TF-IDF cosine search for explicit offline tests."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

from tools.shared.dietary import matches_diet
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
        from tools.shared.alloydb_client import get_alloydb

        emb = get_embeddings()
        q = emb.embed(query_text)

        candidates: list[dict] = []
        for p in get_alloydb().list_inventory(store_id):
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
                if not matches_diet(p, dietary_preference):
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
    """Exact pgvector cosine search with hard stock, diet, and price filters."""

    def nearest_in_stock(self, *, query_text: str, store_id: str, dietary_preference: str,
                         max_price_aed: float, min_price_aed: float = 0.0,
                         exclude_product_id: str | None = None, limit: int = 1) -> list[dict]:
        from sqlalchemy import text

        from tools.shared.database import get_engine

        vector = get_embeddings().embed(query_text)
        price = "CASE WHEN discount_active THEN price_aed * (1 - COALESCE(discount_pct,0)/100) ELSE price_aed END"
        sql = f"""SELECT product_id, product_name, category, dietary_flags, attributes, source_attributes->>'ingredients' AS ingredients, {price} AS price_aed,
            1 - (embedding <=> CAST(:vector AS vector)) AS similarity_score
            FROM inventory WHERE store_id=:store AND stock_quantity > 0 AND embedding IS NOT NULL
            AND (CAST(:excluded AS TEXT) IS NULL OR product_id != :excluded)
            AND (:diet='none' OR :diet=ANY(string_to_array(dietary_flags, ',')) OR (:diet='halal' AND (category<>'halal_meat' OR attributes->>'protein_type'='seafood')))
            AND {price} >= :minimum AND (CAST(:maximum AS NUMERIC)=0 OR {price} <= :maximum)
            ORDER BY embedding <=> CAST(:vector AS vector) LIMIT :limit"""
        with get_engine().connect() as conn:
            rows = conn.execute(text(sql), {"vector": str(vector), "store": store_id,
                "excluded": exclude_product_id, "diet": dietary_preference or "none",
                "minimum": min_price_aed, "maximum": max_price_aed, "limit": max(100, limit * 10)}).mappings()
            return [{**dict(row), "price_aed": float(row["price_aed"]),
                     "similarity_score": float(row["similarity_score"])} for row in rows
                    if matches_diet(dict(row), dietary_preference)][:limit]


def get_vector_search() -> VectorSearch:
    return MockVectorSearch() if settings.use_mock else RealVectorSearch()
