"""suggest_substitution — SPEC-ARIA-05 (v1.1: graceful degradation + history).

Finds the best in-stock alternative via semantic vector search (AlloyDB AI /
ScaNN in prod, TF-IDF cosine in mock). Dietary preference is a HARD filter.
Price (±20%) and purchase history are PREFERENCES with graceful fallback, so
the tool behaves sensibly for arbitrary inputs:

  Tier 1: in price band + in purchase history  (first preference)
  Tier 2: in price band
  Tier 3: out of band but dietary-safe + in stock (offered as an option)
  None  : no dietary-safe in-stock candidate -> null + operational event
          ("new" | "recurring") so the store manager / PULSE can act.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from tools.shared.alloydb_client import get_alloydb
from tools.shared.bigquery_client import get_bigquery
from tools.shared.embeddings import product_document
from tools.shared.errors import error
from tools.shared.logger import get_logger
from tools.shared.rate_limit import limiter
from tools.shared.settings import settings
from tools.shared.vector_search import get_vector_search

logger = get_logger("aria.suggest_substitution")
router = APIRouter()

_VALID_DIET = {"halal", "vegetarian", "vegan", "none"}
# A substitute must be at least this semantically similar to the original,
# else it is not a real substitute regardless of price/history.
_MIN_SIMILARITY = 0.05


def _null_result(reason: str, event: str | None) -> dict:
    return {
        "substitute_product_id": None,
        "name": None,
        "price_aed": None,
        "similarity_score": 0.0,
        "reason": reason,
        "in_stock": False,
        "in_band": False,
        "out_of_price_range": False,
        "from_purchase_history": False,
        "substitution_event": event,
    }


def suggest_substitution(
    product_id: str,
    store_id: str,
    dietary_preference: str,
    max_price_aed: float,
    customer_id: str | None = None,
) -> dict:
    """
    Finds the best in-stock, dietary-safe alternative for an out-of-stock
    product. Prefers items within ±20% of the original price and items the
    customer has ordered before. Falls back to offering an out-of-band option,
    and if nothing fits, flags an operational event for the store team.
    Call immediately when check_stock() returns available=False.
    """
    if dietary_preference not in _VALID_DIET:
        return error("VALIDATION_ERROR", f"invalid dietary_preference: {dietary_preference}")
    if max_price_aed is None or max_price_aed <= 0:
        return error("VALIDATION_ERROR", "max_price_aed must be > 0")

    db = get_alloydb()
    original = db.get_product(product_id)
    if not original:
        return error("NOT_FOUND", f"product {product_id} not found")

    orig_price = float(original["price_aed"])
    band_floor = orig_price * 0.80
    band_ceiling = orig_price * 1.20

    # Purchase history for personalization (optional).
    history: set[str] = set()
    if customer_id:
        cust = db.get_customer(customer_id)
        if cust:
            history = {o["product_id"] for o in cust.get("last_orders", [])}

    # Gather dietary-safe, in-stock candidates WITHOUT a hard price filter
    # (price is scored into tiers below). max_price_aed acts as an absolute
    # upper bound so we never suggest something the caller forbids outright.
    candidates = get_vector_search().nearest_in_stock(
        query_text=product_document(original),
        store_id=store_id,
        dietary_preference=dietary_preference,
        max_price_aed=max_price_aed,
        min_price_aed=0.0,
        exclude_product_id=product_id,
        limit=10,
    )

    if not candidates:
        event = get_bigquery().record_substitution_gap(product_id=product_id, store_id=store_id)
        logger.info("suggest_substitution", tool="suggest_substitution", product_id=product_id,
                    substitute_found=False, substitution_event=event, status="success")
        return _null_result(
            "No suitable in-stock alternative — flagged to the store team", event
        )

    # Semantic relevance is the PRIMARY gate: a substitute must actually be
    # similar to the original, else it's not a substitute no matter its price.
    # This keeps results sensible for arbitrary inputs (no dairy-for-rice).
    relevant = [c for c in candidates if c["similarity_score"] >= _MIN_SIMILARITY]
    if not relevant:
        event = get_bigquery().record_substitution_gap(product_id=product_id, store_id=store_id)
        logger.info("suggest_substitution", tool="suggest_substitution", product_id=product_id,
                    substitute_found=False, substitution_event=event, status="success")
        return _null_result(
            "No semantically comparable in-stock alternative — flagged to the store team", event
        )

    # Score = similarity, boosted when in the ±20% price band and/or in the
    # customer's purchase history. Similarity dominates; band/history break ties
    # and nudge otherwise-close candidates.
    def _rank_score(c: dict) -> float:
        s = c["similarity_score"]
        if band_floor <= c["price_aed"] <= band_ceiling:
            s += 0.10
        if c["product_id"] in history:
            s += 0.15
        return s

    relevant.sort(key=_rank_score, reverse=True)
    best = relevant[0]
    verified_reason = None
    if not settings.use_mock:
        from tools.shared.substitution_match import choose_substitute

        try:
            match = choose_substitute(original, relevant)
        except Exception:
            return error("UPSTREAM_ERROR", "Google could not verify a suitable substitute; please retry", True)
        if match.product_id is None:
            event = get_bigquery().record_substitution_gap(product_id=product_id, store_id=store_id)
            return _null_result("No functionally equivalent in-stock substitute found", event)
        best = next(c for c in relevant if c["product_id"] == match.product_id)
        verified_reason = match.explanation

    in_band = band_floor <= best["price_aed"] <= band_ceiling
    from_history = best["product_id"] in history
    sub = db.get_product_at_store(best["product_id"], store_id) or db.get_product(best["product_id"])
    cat = (sub["category"] if sub else "grocery").replace("_", " ")

    if in_band:
        reason = f"Similar {cat}, matches {dietary_preference} preference, within your usual price range"
        if from_history:
            reason += " — and you've ordered it before"
    else:
        reason = (
            f"Closest {dietary_preference}-friendly {cat} in stock, but priced "
            f"outside your original range — your call"
        )
        if from_history:
            reason += " (you've bought this before)"

    if verified_reason:
        reason = verified_reason + (" Outside the original price range." if not in_band else "")

    score = max(0.0, min(1.0, best["similarity_score"]))
    result = {
        "substitute_product_id": best["product_id"],
        "name": best["product_name"],
        "price_aed": float(best["price_aed"]),
        "similarity_score": round(score, 4),
        "reason": reason,
        "in_stock": True,
        "in_band": in_band,
        "out_of_price_range": not in_band,
        "from_purchase_history": from_history,
        "substitution_event": None,
    }
    logger.info(
        "suggest_substitution",
        tool="suggest_substitution",
        product_id=product_id,
        substitute_found=True,
        in_band=in_band,
        from_history=from_history,
        similarity_score=result["similarity_score"],
        status="success",
    )
    return result


class SubstitutionRequest(BaseModel):
    product_id: str
    store_id: str
    dietary_preference: str
    max_price_aed: float
    customer_id: str | None = None


@router.post("/tools/suggest-substitution")
@limiter.limit("60/minute")
async def suggest_substitution_endpoint(request: Request, req: SubstitutionRequest) -> dict:
    return suggest_substitution(
        req.product_id, req.store_id, req.dietary_preference, req.max_price_aed, req.customer_id
    )
