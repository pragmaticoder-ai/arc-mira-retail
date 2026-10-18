"""Apply product labels only where relevant to MIRA's shopping policy."""

from __future__ import annotations


def matches_diet(product: dict, dietary: str) -> bool:
    if not dietary or dietary == "none":
        return True
    # MIRA's halal preference constrains meat products. It is not a global
    # certification requirement for rice, produce or other grocery categories.
    if dietary == "halal" and product.get("category") != "halal_meat":
        return True
    flags = {f.strip().lower() for f in (product.get("dietary_flags") or "").split(",")}
    if dietary == "halal" and (
        {"non_halal", "not_halal"} & flags
        or (product.get("attributes") or {}).get("halal") in (False, "false")
    ):
        return False
    return dietary in flags


def dietary_message(product: dict, dietary: str) -> str:
    if dietary == "halal":
        return f"{product['product_name']} has no verified halal meat label in the catalog. Choose meat with a verified halal label."
    return f"Cannot verify {dietary} suitability for {product['product_name']} from the catalog information. Choose a verified alternative or review your dietary preference."
