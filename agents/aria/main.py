"""ARIA agent HTTP service — Cloud Run entry point.

Exposes POST /aria/chat in the Agent API contract shape consumed by the
frontend (frontend/aria-app). In mock mode (USE_MOCK=true, default) it runs a
deterministic orchestration over the real ARIA tool functions and captures the
ReAct chain, so the full flow works offline. With USE_MOCK=false it delegates
to the ADK agent (agents.aria.agent.get_agent()).
"""

from __future__ import annotations

import uuid

from fastapi import FastAPI
from pydantic import BaseModel

from tools.aria_tools.apply_promotion import apply_promotion
from tools.aria_tools.build_cart import build_cart
from tools.aria_tools.check_stock import check_stock
from tools.aria_tools.get_customer_context import get_customer_context
from tools.aria_tools.log_session import log_session
from tools.aria_tools.suggest_substitution import suggest_substitution
from tools.shared.errors import is_error
from tools.shared.logger import get_logger
from tools.shared.settings import settings

logger = get_logger("aria.agent")
app = FastAPI(title="ARC ARIA Agent", version="1.0.0")

_CONFIRM = {"confirm", "yes", "place order", "go ahead", "proceed"}


class ChatRequest(BaseModel):
    session_id: str | None = None
    customer_id: str = "sarah_123"
    store_id: str = "dubai_marina_01"
    message: str


def _step(kind: str, text: str) -> dict:
    return {"type": kind, "text": text}


def _cart_state(items: list[dict], promo: dict | None) -> dict:
    subtotal = round(sum(i["price_aed"] * i["quantity"] for i in items), 2)
    applied = None
    total = subtotal
    if promo and promo.get("promotion_applied"):
        applied = {
            "promotion_id": promo["promotion_id"],
            "promotion_name": promo["promotion_name"],
            "discount_aed": promo["discount_aed"],
            "new_total_aed": promo["new_total_aed"],
        }
        total = promo["new_total_aed"]
    return {"items": items, "total_aed": total, "promotion": applied}


def _orchestrate(req: ChatRequest) -> dict:
    """Deterministic mock orchestration following ARIA's sequencing rules."""
    sid = req.session_id or str(uuid.uuid4())
    reasoning: list[dict] = []
    msg = req.message.strip().lower()

    # ── Confirmation → place order + log session ─────────────────────
    if any(msg == c or msg.startswith(c) for c in _CONFIRM):
        # Rebuild the demo cart deterministically.
        ctx = get_customer_context(req.customer_id)
        cart = build_cart("weekly groceries", ctx["dietary_preference"],
                          ctx["weekly_budget_aed"], ctx["household_size"], req.store_id)
        promo = apply_promotion(cart["items"], cart["total_aed"], ctx["dietary_preference"], req.store_id)
        from tools.aria_tools.place_order import place_order
        state = _cart_state(cart["items"], promo)
        order = place_order(req.customer_id, req.store_id, cart["items"],
                            promo.get("promotion_id"), state["total_aed"])
        reasoning += [
            _step("THOUGHT", "Customer confirmed. Placing the order."),
            _step("ACTION", "place_order(...)"),
            _step("OBSERVATION", f"Order {order['order_id']} created, status={order['status']}."),
            _step("ACTION", "log_session(...)"),
        ]
        log_session(sid, req.customer_id, req.store_id, cart["items"],
                    cart["items_unavailable"], [], promo.get("promotion_id"),
                    promo.get("discount_aed", 0.0), state["total_aed"],
                    ctx["weekly_budget_aed"], "positive", True)
        reasoning.append(_step("OBSERVATION", "Session logged to the BigQuery bridge."))
        return {
            "reply": (
                f"Order placed. Total AED {order['total_aed']:.2f}, delivery "
                f"{order['estimated_delivery_window']}. I logged this session for the ops team."
            ),
            "cart": state,
            "reasoning": reasoning,
            "order": {
                "order_id": order["order_id"],
                "status": order["status"],
                "total_aed": order["total_aed"],
                "estimated_delivery_window": order["estimated_delivery_window"],
            },
            "session_logged": True,
        }

    # ── Default: build a cart (the main flow) ────────────────────────
    reasoning.append(_step("ACTION", f"get_customer_context(customer_id='{req.customer_id}')"))
    ctx = get_customer_context(req.customer_id)
    if is_error(ctx):
        return {"reply": "I couldn't find your profile. Please sign in again.",
                "cart": {"items": [], "total_aed": 0, "promotion": None},
                "reasoning": reasoning, "order": None, "session_logged": False}
    reasoning.append(_step("OBSERVATION",
        f"dietary={ctx['dietary_preference']}, household={ctx['household_size']}, budget=AED {ctx['weekly_budget_aed']:.0f}"))

    reasoning.append(_step("ACTION", "build_cart(...)"))
    cart = build_cart("weekly groceries", ctx["dietary_preference"],
                      ctx["weekly_budget_aed"], ctx["household_size"], req.store_id)
    reasoning.append(_step("OBSERVATION",
        f"{len(cart['items'])} items, AED {cart['total_aed']:.2f}, "
        f"{len(cart['items_unavailable'])} unavailable"))

    # Surface the brown-rice stockout + substitution for the demo.
    stock = check_stock("rice_brown_500g", req.store_id)
    sub_note = ""
    if not stock["available"]:
        reasoning.append(_step("ACTION", "suggest_substitution(product_id='rice_brown_500g', ...)"))
        sub = suggest_substitution("rice_brown_500g", req.store_id, ctx["dietary_preference"], 11.4)
        if sub.get("substitute_product_id"):
            sub_note = f" Brown rice was out of stock, so I suggest {sub['name']} instead."
            reasoning.append(_step("OBSERVATION", f"Substitute: {sub['name']} ({sub['reason']})"))

    reasoning.append(_step("ACTION", "apply_promotion(...)"))
    promo = apply_promotion(cart["items"], cart["total_aed"], ctx["dietary_preference"], req.store_id)
    if promo.get("promotion_applied"):
        reasoning.append(_step("OBSERVATION",
            f"{promo['promotion_name']} applied, saving AED {promo['discount_aed']:.2f}"))

    state = _cart_state(cart["items"], promo)
    reply = (
        f"I built your {ctx['dietary_preference']} cart for a household of "
        f"{ctx['household_size']}.{sub_note} Total is AED {state['total_aed']:.2f} "
        f"of your AED {ctx['weekly_budget_aed']:.0f} budget. Say 'confirm' to place the order."
    )
    return {"reply": reply, "cart": state, "reasoning": reasoning,
            "order": None, "session_logged": False}


@app.post("/aria/chat")
async def aria_chat(req: ChatRequest) -> dict:
    logger.info("aria_chat", customer_id=req.customer_id, use_mock=settings.use_mock)
    if settings.use_mock:
        return _orchestrate(req)
    # Real path: delegate to the ADK agent.
    from agents.aria.agent import get_agent

    get_agent()  # NOTE(backend): run the ADK agent and map output to the contract shape
    raise NotImplementedError("Real ADK run wiring pending; set USE_MOCK=true.")


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "arc-aria-agent", "mode": "mock" if settings.use_mock else "live"}
