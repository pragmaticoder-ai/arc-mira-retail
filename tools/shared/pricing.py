"""Authoritative product prices and typed basket validation."""
from __future__ import annotations

import math

from tools.shared.alloydb_client import get_alloydb
from tools.shared.dietary import dietary_message, matches_diet
from tools.shared.errors import error, is_error


def effective_price(product: dict) -> float:
    discount = product.get("discounted_price_aed")
    return float(discount if product.get("discount_active") and discount is not None else product["price_aed"])


def canonical_items(cart: list[dict], store_id: str, dietary: str = "none", *, check_stock: bool = True) -> dict:
    if not isinstance(cart, list) or not cart or len(cart) > 100:
        return error("VALIDATION_ERROR", "Cart must contain 1–100 products")
    quantities: dict[str, int] = {}
    for item in cart:
        if not isinstance(item, dict):
            return error("VALIDATION_ERROR", "Invalid cart item")
        pid, qty = item.get("product_id"), item.get("quantity")
        if not isinstance(pid, str) or type(qty) is not int or not 1 <= qty <= 1000:
            return error("VALIDATION_ERROR", "Each quantity must be a positive integer, at most 1000")
        quantities[pid] = quantities.get(pid, 0) + qty
        if quantities[pid] > 1000:
            return error("VALIDATION_ERROR", "Combined quantity exceeds 1000")
    db = get_alloydb()
    items = []
    for pid, qty in quantities.items():
        p = db.get_product_at_store(pid, store_id)
        if not p:
            return error("NOT_FOUND", f"Product {pid} not found at this store")
        if not matches_diet(p, dietary):
            return error("VALIDATION_ERROR", dietary_message(p, dietary))
        if check_stock and qty > p["stock_quantity"]:
            return error("VALIDATION_ERROR", f"Insufficient stock for {p['product_name']}")
        items.append({"product_id": pid, "product_name": p["product_name"], "quantity": qty,
                      "price_aed": effective_price(p), "aisle_ref": p["aisle_ref"],
                      "in_stock": p["stock_quantity"] >= qty,
                      "discount_active": bool(p.get("discount_active")),
                      "substituted": any(i.get("substituted", False) for i in cart if i.get("product_id") == pid)})
    return {"items": items, "total_aed": round(sum(i["quantity"] * i["price_aed"] for i in items), 2)}


def quote_cart(cart: list[dict], store_id: str, dietary: str, *, promotion_id: str | None = None,
               select_promotion: bool = True) -> dict:
    from tools.aria_tools.apply_promotion import apply_promotion

    result = canonical_items(cart, store_id, dietary)
    if is_error(result):
        return result
    promo = None
    if select_promotion or promotion_id:
        applied = apply_promotion(result["items"], result["total_aed"], dietary, store_id,
                                  promotion_id=promotion_id)
        if is_error(applied):
            return applied
        if promotion_id and not applied["promotion_applied"]:
            return error("VALIDATION_ERROR", "Promotion is no longer eligible")
        if applied["promotion_applied"]:
            promo = {k: applied[k] for k in ("promotion_id", "promotion_name", "discount_aed", "new_total_aed")}
    return {"items": result["items"], "promotion": promo,
            "total_aed": promo["new_total_aed"] if promo else result["total_aed"]}


def valid_amount(value: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0
