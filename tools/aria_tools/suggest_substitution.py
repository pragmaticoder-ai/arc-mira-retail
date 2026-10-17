"""suggest_substitution — SPEC-ARIA-05.

Finds the most semantically similar in-stock alternative via the vector search
adapter (AlloyDB AI / ScaNN in prod, cosine-over-seed in mock). Respects
dietary preference and price ceiling. Never returns the original product.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.errors import error
from tools.shared.logger import get_logger
from tools.shared.vector_search import get_vector_search

logger = get_logger("aria.suggest_substitution")
router = APIRouter()

_VALID_DIET = {"halal", "vegetarian", "vegan", "none"}


def suggest_substitution(
    product_id: str,
    store_id: str,
    dietary_preference: str,
    max_price_aed: float,
) -> dict:
    """
    Uses vector search to find semantically similar in-stock products matching
    dietary_preference and within max_price_aed. Returns substitute_product_id,
    name, price_aed, similarity_score, reason. Call immediately when
    check_stock() returns available=False.
    """
    if dietary_preference not in _VALID_DIET:
        return error("VALIDATION_ERROR", f"invalid dietary_preference: {dietary_preference}")
    if max_price_aed is None or max_price_aed <= 0:
        return error("VALIDATION_ERROR", "max_price_aed must be > 0")

    db = get_alloydb()
    original = db.get_product(product_id)
    if not original:
        return error("NOT_FOUND", f"product {product_id} not found")

    query_text = f"{original['product_name']} {original['category']} {original['dietary_flags']}"
    results = get_vector_search().nearest_in_stock(
        query_text=query_text,
        store_id=store_id,
        dietary_preference=dietary_preference,
        max_price_aed=max_price_aed,
        exclude_product_id=product_id,
        limit=1,
    )

    if not results:
        return {
            "substitute_product_id": None,
            "name": None,
            "price_aed": None,
            "similarity_score": 0.0,
            "reason": "No suitable substitution found within price range",
            "in_stock": False,
        }

    best = results[0]
    sub = db.get_product(best["product_id"])
    reason = (
        f"Similar {sub['category'].replace('_', ' ')} product, "
        f"matches {dietary_preference} preference, within your price range"
    )
    score = max(0.0, min(1.0, best["similarity_score"]))
    result = {
        "substitute_product_id": best["product_id"],
        "name": best["product_name"],
        "price_aed": float(best["price_aed"]),
        "similarity_score": round(score, 4),
        "reason": reason,
        "in_stock": True,
    }
    logger.info(
        "suggest_substitution",
        tool="suggest_substitution",
        product_id=product_id,
        substitute_found=True,
        similarity_score=result["similarity_score"],
        status="success",
    )
    return result


class SubstitutionRequest(BaseModel):
    product_id: str
    store_id: str
    dietary_preference: str
    max_price_aed: float


@router.post("/tools/suggest-substitution")
async def suggest_substitution_endpoint(req: SubstitutionRequest) -> dict:
    return suggest_substitution(
        req.product_id, req.store_id, req.dietary_preference, req.max_price_aed
    )
