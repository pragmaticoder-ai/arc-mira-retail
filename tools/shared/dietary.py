"""Apply product labels only where relevant to MIRA's shopping policy."""

from __future__ import annotations

import re

# Catalog classification, not a claim of religious certification. Land-animal
# ingredients take precedence for mixed products such as chicken/fish dumplings.
_LAND = re.compile(
    r"\b(chicken|poultry|turkey|duck|goose|beef|veal|lamb|mutton|goat|pork|bacon|ham|sausage|salami|pepperoni)\b",
    re.I,
)
_SEAFOOD = re.compile(
    r"\b(tuna|salmon|sardines?|mackerel|anchov(?:y|ies)|fish|seafood|prawns?|shrimps?|crab|lobster|squid|calamari|octopus|mussels?|clams?|oysters?|cod|haddock|tilapia|seabass|seabream|hammour|kingfish|pomfret|snapper|trout|herring)\b",
    re.I,
)


def protein_type(product: dict) -> str:
    if product.get("category") != "halal_meat":
        return "other"
    attrs = product.get("attributes") or {}
    evidence = " ".join(
        str(v or "")
        for v in (
            product.get("product_name"),
            attrs.get("product_type"),
            product.get("source_category"),
            product.get("ingredients"),
        )
    )
    if _LAND.search(evidence):
        return "land_meat"
    if _SEAFOOD.search(evidence):
        return "seafood"
    return "unknown"


def requires_halal_meat_label(product: dict) -> bool:
    return (
        product.get("category") == "halal_meat" and protein_type(product) != "seafood"
    )


def matches_diet(product: dict, dietary: str) -> bool:
    if not dietary or dietary == "none":
        return True
    # MIRA's halal preference constrains meat products. It is not a global
    # certification requirement for rice, produce or other grocery categories.
    if dietary == "halal" and not requires_halal_meat_label(product):
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
