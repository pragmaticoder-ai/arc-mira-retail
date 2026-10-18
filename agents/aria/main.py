"""ARIA: Gemini shopping proposals with server-controlled quotes and checkout."""
from __future__ import annotations

import copy
import json
import re
import uuid
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from tools.aria_tools.build_cart import build_cart
from tools.aria_tools.get_customer_context import get_customer_context
from tools.aria_tools.log_session import log_session
from tools.aria_tools.parse_intent import parse_intent
from tools.aria_tools.place_order import place_order
from tools.aria_tools.suggest_substitution import suggest_substitution
from tools.shared.alloydb_client import get_alloydb
from tools.shared.demand import classify_feedback, signal
from tools.shared.dietary import dietary_message, matches_diet
from tools.shared.errors import is_error
from tools.shared.pricing import canonical_items, quote_cart
from tools.shared.settings import settings

app = FastAPI(title="ARC ARIA", version="1.1.0")
_CONFIRM = {"confirm", "yes", "place order", "go ahead", "proceed", "confirm order"}
_CANCEL = {"cancel", "cancel order", "never mind", "stop", "leave", "end session"}
_ALIASES = {"rice_brown_500g": ("brown rice",), "rice_basmati_5kg": ("basmati", "white rice"),
            "milk_almarai_2l": ("milk",), "laban_almarai_1l": ("laban",), "eggs_dozen": ("eggs",),
            "chicken_whole_1kg": ("chicken",), "tomato_1kg": ("tomato", "tomatoes"),
            "onion_1kg": ("onion", "onions"), "banana_1kg": ("banana", "bananas"),
            "pasta_barilla_500g": ("pasta", "penne"), "bread_white_loaf": ("bread",),
            "oil_sunflower_1_8l": ("sunflower oil",)}


class ChatRequest(BaseModel):
    session_id: uuid.UUID | None = None
    customer_id: str = "sarah_123"
    store_id: str = "dubai_marina_01"
    message: str = Field(min_length=1, max_length=1000)
    cart: list[dict] | None = None
    quote_id: str | None = None
    feedback: Literal["satisfied", "compromise", "rejected"] | None = None
    product_id: str | None = None


def _unwrap(result: dict) -> dict:
    if is_error(result):
        raise HTTPException(502 if result.get("error_code") == "UPSTREAM_ERROR" else 400, detail=result["error_message"])
    return result


def _empty() -> dict:
    return {"items": [], "total_aed": 0.0, "promotion": None}


def _quote(state: dict, items: list[dict]) -> None:
    db = get_alloydb()
    for item in items:
        pid = item.get("product_id")
        if not isinstance(pid, str):
            raise HTTPException(400, "Each basket item requires a product ID")
        product = db.get_product_at_store(pid, state["store_id"])
        if item.get("product_id") in state.get("excluded_ids", []) or (product and product["category"] in state.get("excluded_categories", [])):
            raise HTTPException(400, "This basket contains a product you asked to exclude")
    state["cart"] = _unwrap(quote_cart(items, state["store_id"], state["dietary"])) if items else _empty()
    if state["cart"]["total_aed"] > state["budget"]:
        raise HTTPException(400, "This basket exceeds your budget; remove an item or increase your budget")
    state["quote_id"] = str(uuid.uuid4())


def _log(state: dict, order_placed: bool, reason: str | None = None) -> bool:
    promo = state["cart"].get("promotion") or {}
    logged = log_session(state["session_id"], state["customer_id"], state["store_id"],
        state["cart"]["items"] if order_placed else [], state["unavailable"], state["substitutions"],
        promo.get("promotion_id"), promo.get("discount_aed", 0), state["cart"]["total_aed"],
        state["budget"], "neutral", order_placed, reason, demand_signals=state["demand_signals"],
        requested_items=state["requested_items"])
    return not is_error(logged) and logged.get("logged") is True


def _response(state: dict, reply: str, steps: list[dict] | None = None, *, cart_changed: bool = True) -> dict:
    return {"session_id": state["session_id"], "reply": reply, "cart": state["cart"], "cart_changed": cart_changed,
            "quote_id": state.get("quote_id"), "reasoning": steps or [], "order": state.get("order"),
            "session_logged": state.get("session_logged", False), "demand_signals": state["demand_signals"],
            "substitution_offers": state.get("offers", []), "mode": "local_rules" if settings.use_mock else "google"}


def _feedback(state: dict, req: ChatRequest, outcome: str) -> str:
    offers = [o for o in state.get("offers", []) if req.product_id is None or o["product_id"] == req.product_id]
    if not offers:
        return "There is no pending substitution to rate. Tell me which product you need."
    if len(offers) > 1 and req.product_id is None:
        return "Please choose a substitution using its feedback buttons so I record the right product."
    if req.cart is not None:
        _quote(state, req.cart)
    offer = offers[0]
    pid = offer["product_id"]
    if outcome in {"satisfied", "compromise"} and offer.get("substitute_product_id"):
        items = list(state["cart"]["items"])
        sub = offer["substitute_product_id"]
        if not any(i["product_id"] == sub for i in items):
            items.append({"product_id": sub, "quantity": offer["quantity"], "substituted": True})
        _quote(state, items)
        state["substitutions"] = [s for s in state["substitutions"] if s["original_product_id"] != pid]
        state["substitutions"].append({"original_product_id": pid, "substitute_product_id": sub, "accepted": True})
    elif outcome == "rejected":
        sub = offer.get("substitute_product_id")
        _quote(state, [i for i in state["cart"]["items"] if not (i["product_id"] == sub and i.get("substituted"))])
        state["substitutions"] = [s for s in state["substitutions"] if s["original_product_id"] != pid]
    evidence = req.message if req.feedback is None else f"Customer selected {outcome}: {req.message}"
    state["demand_signals"] = [s for s in state["demand_signals"] if s["product_id"] != pid]
    state["demand_signals"].append(signal(offer, outcome, evidence, offer.get("substitute_product_id")))
    offer["outcome"] = outcome
    state["session_logged"] = _log(state, False)
    return {"compromise": "I recorded this as a temporary compromise. Your original preference stays visible to the store team.",
            "satisfied": "I recorded that the alternative meets your needs.",
            "rejected": "I removed that substitute and recorded that your original need remains unresolved."}[outcome] + " Review the basket before confirming."


def _live_shopping(state: dict, req: ChatRequest) -> dict:
    from agents.google_runtime import plan_shopping

    db = get_alloydb()
    from tools.catalog.service import planner_candidates

    retained = {i["product_id"] for i in state.get("cart", {}).get("items", [])} | set(state.get("requested_items", []))
    catalog = planner_candidates(req.store_id, req.message, retained)
    try:
        plan = plan_shopping(req.message, state, catalog)
    except Exception as exc:
        raise HTTPException(502, "Google shopping planner failed; check model access and server logs") from exc
    # Give the model one bounded correction attempt before mutating business
    # state. Failed proposals cannot leave a partial basket or demand events.
    for attempt in range(2):
        if plan.action != "update_cart":
            break
        products = {p["product_id"]: p for p in catalog}
        if any(i.product_id not in products for i in plan.items) or any(pid not in products for pid in plan.requested_ids):
            raise HTTPException(502, "Planner returned a product outside this store catalog")
        if re.search(r"\bbrown\s+rice\b",req.message,re.I):
            matching=[p for p in catalog if p["category"]=="grains" and re.search(r"\bbrown\s+(?:basmati\s+)?rice\b",p["product_name"],re.I)
                and matches_diet(p,plan.dietary) and p["product_id"] not in plan.excluded_ids and p["category"] not in plan.excluded_categories]
            if matching and not any(p["stock_quantity"]>0 for p in matching):
                original=min(matching,key=lambda p:p["product_id"])
                plan.requested_ids=list(dict.fromkeys([*plan.requested_ids,original["product_id"]]))
                # Do not silently replace a requested grain with a different rice.
                plan.items=[item for item in plan.items if not re.search(r"\brice\b",products[item.product_id]["product_name"],re.I)]
        draft = copy.deepcopy(state)
        draft.update(dietary=plan.dietary,budget=plan.budget,household=plan.household,
            excluded_ids=plan.excluded_ids,excluded_categories=plan.excluded_categories)
        try:
            _quote(draft, [i.model_dump() for i in plan.items])
            if re.search(r"\bbrown\s+rice\b", req.message, re.I):
                available = [p for p in catalog if re.search(r"\bbrown\s+(?:basmati\s+)?rice\b",p["product_name"],re.I)
                    and p["stock_quantity"]>0 and matches_diet(p,plan.dietary)
                    and p["product_id"] not in plan.excluded_ids and p["category"] not in plan.excluded_categories]
                if available and not any(i.product_id in {p["product_id"] for p in available} for i in plan.items):
                    raise HTTPException(400, "Include the explicitly requested in-stock brown rice. Available IDs: "+", ".join(p["product_id"] for p in available[:8]))
            break
        except HTTPException as exc:
            if attempt or exc.status_code != 400:
                raise
            feedback_state = {**state,"planner_validation_feedback":str(exc.detail)}
            try:
                plan = plan_shopping(req.message,feedback_state,catalog)
            except Exception as retry_error:
                raise HTTPException(502,"The shopping planner could not correct its basket; please retry") from retry_error
    state["conversation"] = (state.get("conversation", []) + [
        {"role": "user", "text": req.message}, {"role": "assistant", "text": plan.reply}])[-12:]
    if plan.action != "update_cart":
        db.save_session(state["session_id"], state)
        return _response(state, plan.reply, cart_changed=False)
    state.update(dietary=plan.dietary, budget=plan.budget, household=plan.household,
                 excluded_ids=plan.excluded_ids, excluded_categories=plan.excluded_categories)
    products = {p["product_id"]: p for p in catalog}
    if any(i.product_id not in products for i in plan.items) or any(pid not in products for pid in plan.requested_ids):
        raise HTTPException(502, "Planner returned a product outside this store catalog")
    notes = []
    for pid in plan.requested_ids:
        product = products[pid]
        if pid in state["excluded_ids"] or product["category"] in state["excluded_categories"]:
            continue
        if not matches_diet(product, state["dietary"]):
            continue
        state["requested_items"] = list({*state["requested_items"], pid})
        if product["stock_quantity"] <= 0:
            if not any(p["product_id"] == pid for p in state["unavailable"]):
                state["unavailable"].append({"product_id": pid, "product_name": product["product_name"]})
            if not any(p["product_id"] == pid for p in state["demand_signals"]):
                state["demand_signals"].append(signal(product, "unknown", req.message))
            if re.search(r"\b(no substitutes?|no alternatives|whole ?grain only)\b", req.message, re.I):
                sub = {}
            else:
                sub = _unwrap(suggest_substitution(pid, req.store_id, state["dietary"], state["budget"], req.customer_id))
            offer = {"product_id": pid, "product_name": product["product_name"], "quantity": 1,
                     "substitute_product_id": sub.get("substitute_product_id"),
                     "substitute_name": sub.get("name"), "outcome": "unknown"}
            state["offers"] = [o for o in state["offers"] if o["product_id"] != pid] + [offer]
            notes.append(f"{product['product_name']} is unavailable. " +
                (f"Alternative: {sub['name']}. Please rate whether it meets your needs." if sub.get("substitute_product_id") else "No suitable alternative was found."))
    _quote(state, [i.model_dump() for i in plan.items])
    state["session_logged"] = _log(state, False)
    weekly = bool(re.search(r"\b(weekly|groceries)\b",req.message,re.I))
    summary = (f"Here is a proposed weekly starter basket for {state['household']} people, within your AED {state['budget']:.2f} budget. "
        if weekly else "Your proposed basket is ready. ")
    # Only server-validated basket facts belong in a cart update reply. The
    # model's free text can otherwise contradict prices or claim missing items.
    reply = summary + " ".join(notes) + f" Basket total: AED {state['cart']['total_aed']:.2f}. Review before confirming."
    state["conversation"][-1] = {"role":"assistant","text":reply}
    db.save_session(state["session_id"],state)
    return _response(state, reply,
        [{"type": "ACTION", "text": "Gemini planned against the PostgreSQL catalog; the server validated stock, diet, exclusions, budget and current prices."}])



def _orchestrate(req: ChatRequest) -> dict:
    db = get_alloydb()
    sid = str(req.session_id or uuid.uuid4())
    msg = req.message.strip().lower().replace("’", "'")
    if not msg:
        raise HTTPException(400, "Message cannot be blank")
    with db.transaction():
        ctx = _unwrap(get_customer_context(req.customer_id))
        state = db.get_session(sid)
        if state and (state["customer_id"] != req.customer_id or state["store_id"] != req.store_id):
            raise HTTPException(409, "Start a new session when changing customer or store")
        if state and state.get("order"):
            state["session_logged"] = _log(state, True)
            db.save_session(sid, state)
            return _response(state, "This session already has a confirmed order. Start a new session to shop again.")
        if state and state.get("closed"):
            return _response(state, "This session is closed. Start a new session to shop again.")
        if state is None:
            state = {"session_id": sid, "customer_id": req.customer_id, "store_id": req.store_id,
                     "dietary": ctx["dietary_preference"], "budget": ctx["weekly_budget_aed"],
                     "household": ctx["household_size"], "cart": _empty(), "unavailable": [],
                     "substitutions": [], "demand_signals": [], "requested_items": [], "offers": []}
        if msg in _CANCEL or re.search(r"\b(cancel|don't place|do not place)\b", msg):
            state["demand_signals"] = [signal(s, "abandoned", req.message, s.get("substitute_product_id"))
                                       if s["outcome"] in {"unknown", "compromise", "rejected"} else s
                                       for s in state["demand_signals"]]
            state["session_logged"] = _log(state, False, "customer_cancelled")
            state["closed"] = True
            state["cart"] = _empty()
            db.save_session(sid, state)
            return _response(state, "Session ended. No order was placed; I recorded any unmet needs for the store team.")
        outcome = req.feedback or classify_feedback(req.message)
        if (req.feedback or outcome in {"satisfied", "compromise", "rejected"}) and state.get("offers"):
            reply = _feedback(state, req, outcome)
        elif msg in _CONFIRM:
            if req.cart is not None:
                if not req.cart:
                    raise HTTPException(400, "Your basket is empty")
                incoming = _unwrap(canonical_items(req.cart, req.store_id, state["dietary"]))
                old = [(i["product_id"], i["quantity"], i["price_aed"]) for i in state["cart"]["items"]]
                new = [(i["product_id"], i["quantity"], i["price_aed"]) for i in incoming["items"]]
                if sorted(old) != sorted(new):
                    kept = {i["product_id"] for i in incoming["items"]}
                    for item in state["demand_signals"]:
                        if item.get("substitute_product_id") not in kept and item["outcome"] in {"compromise", "satisfied"}:
                            item.update(outcome="unknown", certainty="unknown", evidence="Basket edited; previous substitution feedback needs confirmation")
                    state["substitutions"] = [s for s in state["substitutions"] if s["substitute_product_id"] in kept]
                    _quote(state, req.cart)
                    db.save_session(sid, state)
                    return _response(state, "Your basket changed. Review this updated quote and confirm again.")
            if not state["cart"]["items"]:
                raise HTTPException(400, "Build and review a basket before confirming")
            if not req.quote_id or req.quote_id != state.get("quote_id"):
                db.save_session(sid, state)
                return _response(state, "Please review this basket, then confirm its current quote.")
            current = _unwrap(quote_cart(state["cart"]["items"], req.store_id, state["dietary"]))
            if current != state["cart"]:
                _quote(state, current["items"])
                db.save_session(sid, state)
                return _response(state, "Prices or promotions changed. Review this updated quote and confirm again.")
            promo = state["cart"]["promotion"] or {}
            state["order"] = _unwrap(place_order(req.customer_id, req.store_id, state["cart"]["items"],
                promo.get("promotion_id"), state["cart"]["total_aed"], sid, state["dietary"]))
            ordered_ids = {i["product_id"] for i in state["cart"]["items"]}
            for pid in state["requested_items"]:
                if pid in ordered_ids:
                    product = db.get_product_at_store(pid, req.store_id)
                    state["demand_signals"] = [s for s in state["demand_signals"] if s["product_id"] != pid]
                    assert product is not None
                    state["demand_signals"].append({**signal(product, "fulfilled", "Requested product included in confirmed order"),
                                                     "evidence_source": "order_record", "certainty": "observed"})
            state["session_logged"] = _log(state, True)
            reply = f"Order {state['order']['order_id']} confirmed for AED {state['order']['total_aed']:.2f}. "
            reply += "Your session and original preferences were recorded." if state["session_logged"] else "Session recording needs a retry."
        elif msg in {"sync cart", "review cart"} and req.cart is not None:
            _quote(state, req.cart)
            reply = "Here is your updated basket with current store prices. Review it before confirming."
        elif settings.use_mock and any(w in msg for w in ("discount", "offer")) and "groceries" not in msg and "laban" not in msg:
            products = [p for p in db.list_inventory(req.store_id) if p.get("discount_active") and p["stock_quantity"] > 0]
            reply = "Approved offers: " + "; ".join(f"{p['product_name']}: AED {p['discounted_price_aed']:.2f}" for p in products) if products else "There are no manager-approved discounts at this store yet."
        else:
            if not settings.use_mock:
                return _live_shopping(state, req)
            intent = _unwrap(parse_intent(req.message))
            state["dietary"] = intent["dietary_preference"] if intent["dietary_preference"] != "none" else state["dietary"]
            state["budget"] = intent["budget_aed"] if intent["budget_aed"] is not None else state["budget"]
            state["household"] = intent["household_size"] or state["household"]
            requested = [pid for pid, names in _ALIASES.items() if any(re.search(r"\b" + re.escape(n) + r"\b", msg) for n in names)]
            excluded = []
            for pid, names in _ALIASES.items():
                if any(re.search(r"(?:no|without|exclude|don't want|do not want|remove)\s+(?:any\s+)?" + re.escape(name) + r"\b", msg) for name in names):
                    excluded.append(pid)
            state["excluded_ids"] = list(set(state.get("excluded_ids", []) + excluded))
            requested = [pid for pid in requested if pid not in state["excluded_ids"]]
            if any(phrase in msg for phrase in ("no dairy", "dairy-free", "no meat or dairy")):
                state["excluded_categories"] = list(set(state.get("excluded_categories", []) + ["dairy"]))
            weekly = any(w in msg for w in ("weekly", "groceries", "basket", "breakfast", "biryani", "snack", "party"))
            if not weekly and not requested and req.cart is None:
                db.save_session(sid, state)
                return _response(state, "Tell me a product from the catalog, or ask for weekly groceries with your diet and budget. You can also add products directly to your basket.")
            built = _unwrap(build_cart(intent["goal"], state["dietary"], state["budget"], state["household"], req.store_id)) if weekly or not requested else {"items": []}
            items = [i for i in built["items"] if i["product_id"] not in state["excluded_ids"]
                     and (db.get_product(i["product_id"]) or {}).get("category") not in state.get("excluded_categories", [])]
            requested = [pid for pid in requested if (db.get_product(pid) or {}).get("category") not in state.get("excluded_categories", [])]
            notes = []
            for pid in requested:
                product = db.get_product_at_store(pid, req.store_id)
                if not product:
                    notes.append(f"{pid} is not stocked at this store.")
                    continue
                if not matches_diet(product, state["dietary"]):
                    notes.append(dietary_message(product, state["dietary"]))
                    continue
                state["requested_items"] = list({*state["requested_items"], pid})
                if product["stock_quantity"] > 0:
                    if not any(i["product_id"] == pid for i in items):
                        items.append({"product_id": pid, "quantity": 1})
                else:
                    if not any(i["product_id"] == pid for i in state["unavailable"]):
                        state["unavailable"].append({"product_id": pid, "product_name": product["product_name"]})
                    state["demand_signals"] = [s for s in state["demand_signals"] if s["product_id"] != pid]
                    initial_outcome = "rejected" if classify_feedback(req.message) == "rejected" else "unknown"
                    state["demand_signals"].append(signal(product, initial_outcome, req.message))
                    remaining = max(0, state["budget"] - sum(i.get("price_aed", 0) * i["quantity"] for i in items))
                    sub = suggest_substitution(pid, req.store_id, state["dietary"], max(remaining, 0.01), req.customer_id)
                    if "wholegrain only" in msg or "whole grain only" in msg or "no substitute" in msg:
                        sub = {}
                    offer = {"product_id": pid, "product_name": product["product_name"], "quantity": 1,
                             "substitute_product_id": sub.get("substitute_product_id"), "substitute_name": sub.get("name"), "outcome": "unknown"}
                    state["offers"] = [o for o in state["offers"] if o["product_id"] != pid] + [offer]
                    notes.append(f"{product['product_name']} is unavailable. " +
                        (f"I can offer {sub['name']}; choose whether it meets your needs or is a temporary compromise." if sub.get("substitute_product_id") else "No suitable alternative is available within your constraints."))
            # Canonicalize the budget one item at a time; never silently exceed it.
            affordable: list[dict] = []
            for item in items:
                candidate = _unwrap(canonical_items(affordable + [item], req.store_id, state["dietary"]))
                if candidate["total_aed"] <= state["budget"]:
                    affordable = candidate["items"]
                else:
                    notes.append(f"I left {item.get('product_name', item['product_id'])} out to stay within budget.")
            _quote(state, affordable)
            state["session_logged"] = _log(state, False)
            reply = f"Your {state['dietary']} basket totals AED {state['cart']['total_aed']:.2f} within AED {state['budget']:.2f}. " + " ".join(notes) + " Review the basket before confirming."
        db.save_session(sid, state)
        return _response(state, reply, [{"type": "ACTION", "text": "Validate constraints, reprice the basket and preserve customer evidence."},
                                        {"type": "OBSERVATION", "text": "Local deterministic orchestration; no model-generated reasoning." if settings.use_mock else "Server-validated quote, checkout or explicit customer feedback; no model-generated internal reasoning."}])


@app.post("/aria/chat")
def aria_chat(req: ChatRequest) -> dict:
    return _orchestrate(req)


@app.get("/aria/inventory")
def inventory(store_id: str = "dubai_marina_01") -> dict:
    return {"items": get_alloydb().list_inventory(store_id)}


@app.get("/aria/catalog")
def catalog(store_id: str = "dubai_marina_01", category: str = "all", q: str = Query(default="", max_length=200),
            page: int = Query(default=1, ge=1), page_size: int = Query(default=24, ge=1, le=96),
            sort: str = "name", min_price: float | None = Query(default=None, ge=0),
            max_price: float | None = Query(default=None, ge=0), in_stock: bool = False,
            attributes: str = Query(default="{}", max_length=8000)) -> dict:
    from tools.catalog.service import list_products

    try:
        selected = json.loads(attributes)
        if not isinstance(selected, dict) or len(selected) > 12:
            raise ValueError("Invalid facets")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValueError("Minimum price exceeds maximum price")
        return list_products(store_id=store_id, category=category, q=q, page=page, page_size=page_size,
            sort=sort, min_price=min_price, max_price=max_price, in_stock=in_stock, attributes=selected)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/aria/products/{product_id}")
def product(product_id: str, store_id: str = "dubai_marina_01") -> dict:
    from tools.catalog.service import product_detail

    item = product_detail(product_id, store_id)
    if item is None:
        raise HTTPException(404, "Product not found at this store")
    return item


@app.get("/aria/orders")
def orders(customer_id: str = "sarah_123", store_id: str | None = None,
           page: int = Query(default=1,ge=1), page_size: int = Query(default=20,ge=1,le=50)) -> dict:
    db=get_alloydb()
    with db.transaction():
        if db.get_customer(customer_id) is None:
            raise HTTPException(404,"Customer not found")
        rows=db.list_orders(customer_id,store_id)
        fields=("order_id","status","store_id","items","total_aed","promotion_id","estimated_delivery_window","created_at")
        return {"items":[{k:o.get(k) for k in fields} for o in rows[(page-1)*page_size:page*page_size]],
                "total":len(rows),"page":page,"total_pages":max(1,(len(rows)+page_size-1)//page_size)}


@app.get("/aria/bootstrap")
def bootstrap(customer_id: str = "sarah_123") -> dict:
    db = get_alloydb()
    with db.transaction():
        customer = _unwrap(get_customer_context(customer_id))
        stores = db.list_stores()
        selected = settings.default_store_id or customer["preferred_store"]
        if selected not in {row["store_id"] for row in stores}:
            selected = customer["preferred_store"]
        return {"customer": customer, "stores": stores, "default_store_id": selected}


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "service": "arc-aria",
            "mode": "local_rules" if settings.use_mock else "production"}
