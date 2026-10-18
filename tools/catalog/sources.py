"""Public LuLu SSR data: preserve actual SKU prices and provenance, never invent stock."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlparse

BASE = "https://gcc.luluhypermarket.com"
CATEGORIES = (
    "dairy",
    "grains",
    "halal_meat",
    "vegetables",
    "fruits",
    "beverages",
    "snacks",
    "condiments",
)


def flight_text(html: str) -> str:
    chunks = []
    for match in re.finditer(r"self\.__next_f\.push\((.*?)\)</script>", html, re.S):
        try:
            chunks.extend(v for v in json.loads(match[1]) if isinstance(v, str))
        except (ValueError, TypeError):
            continue
    return "".join(chunks)


def listing(html: str) -> dict:
    text = flight_text(html)
    for match in re.finditer(r'\{"pagination":\{"current_page"', text):
        try:
            data, _ = json.JSONDecoder().raw_decode(text[match.start() :])
            if isinstance(data.get("products"), list):
                return data
        except ValueError:
            continue
    raise ValueError(
        "No public product listing found (empty, unsupported or access-controlled page)"
    )


def category_for(attributes: dict, path: str = "") -> str | None:
    kind = str(attributes.get("lulu_product_type", "")).lower()
    level3 = str(attributes.get("level_3", "")).lower()
    text = " ".join(
        str(attributes.get(k, "")) for k in ("level_2", "level_3", "lulu_product_type")
    ).lower()
    context = text + " " + path.lower()
    if any(
        t in context
        for t in ("pet-food", "household", "beauty", "personal-care", "baby-food")
    ):
        return None
    if "/fresh-food-fruits-vegetables-fruits" in path or level3 in {
        "fruits",
        "fresh fruits",
    }:
        return "fruits"
    if "/fresh-food-fruits-vegetables-vegetables" in path or level3 in {
        "vegetables",
        "fresh vegetables",
    }:
        return "vegetables"
    if any(
        t in kind
        for t in (
            "sauce",
            "dressing",
            "mayonnaise",
            "mustard",
            "ketchup",
            "vinegar",
            "masala",
            "spice",
            "saffron",
            "seasoning",
        )
    ):
        return "condiments"
    if any(
        t in context
        for t in (
            "dairy",
            "cheese",
            "yoghurt",
            "yogurt",
            "laban",
            "long-life-milk",
            "milk-powder",
        )
    ) or ("milk" in kind and "chocolate" not in kind):
        return "dairy"
    if any(
        t in context
        for t in ("meat", "poultry", "seafood", "seafoods", "fish", "burger")
    ):
        return "halal_meat"  # Legacy key only; no halal claim is inferred.
    if any(t in kind for t in ("juice", "coffee", "tea", "water", "energy drink")):
        return "beverages"
    if "fruit" in kind:
        return "fruits"
    if "vegetable" in kind:
        return "vegetables"
    if any(
        t in context
        for t in ("beverage", "juice", "coffee", "tea", "water", "energy-drink")
    ):
        return "beverages"
    if any(
        t in context
        for t in (
            "rice",
            "pasta",
            "noodle",
            "flour",
            "pulse",
            "cereal",
            "oat",
            "grain",
            "lentil",
            "bean",
            "dhal",
        )
    ):
        return "grains"
    if any(
        t in context
        for t in (
            "snack",
            "biscuit",
            "chocolate",
            "bakery",
            "bread",
            "cake",
            "nuts",
            "date",
            "ice-cream",
            "confection",
        )
    ):
        return "snacks"
    if any(
        t in context
        for t in (
            "food cupboard",
            "cooking",
            "oil",
            "sauce",
            "spice",
            "spread",
            "honey",
            "salt",
            "sugar",
            "pickle",
            "condiment",
            "canned",
        )
    ):
        return "condiments"
    return None


def safe_url(value: str) -> str:
    url = urljoin(BASE, value)
    if urlparse(url).scheme != "https" or not urlparse(url).hostname:
        raise ValueError("Invalid catalog URL")
    return url


def normalize(
    product: dict, path: str, captured_at: str, parent: dict | None = None
) -> dict | None:
    attrs = {**(parent or {}).get("attributes", {}), **product.get("attributes", {})}
    category = category_for(attrs, path + " " + str(product.get("absolute_url", "")))
    if not category:
        return None
    try:
        price = Decimal(str(product["price"]))
        if not price.is_finite() or price <= 0:
            return None
        if (
            str(
                product.get("currency_type", (parent or {}).get("currency_type", "aed"))
            ).upper()
            != "AED"
        ):
            return None
        images = [
            safe_url(i["image"])
            for i in product.get("productimage_set", [])
            if i.get("image") and i.get("status", "active") == "active"
        ]
        if not images:
            return None
        name = product["name"].strip()
        source_id = str(product["pk"])
        if not source_id.isdigit() or not name:
            return None
    except (KeyError, ValueError, TypeError, InvalidOperation):
        return None
    flags = [
        k
        for k in ("vegan", "vegetarian", "halal")
        if attrs.get(k) is True or str(attrs.get(k, "")).lower() in {"true", "yes"}
    ]
    if "halal" in name.lower() and "halal" not in flags:
        flags.append("halal")
    pack = (
        attrs.get("content", "")
        if parent is None
        else product.get("attributes", {}).get("content", "")
    )
    if not pack:
        match = re.search(
            r"\d+(?:\.\d+)?\s*(?:[x×]\s*\d+(?:\.\d+)?\s*)?(?:kg|g|ml|litres?|liters?|l|pcs?|pieces?|packs?)\b.*$",
            name,
            re.I,
        )
        pack = match[0] if match else ""
    facets = {
        "brand": str(attrs.get("brand", "Unknown")),
        "product_type": str(attrs.get("lulu_product_type", "")),
        "pack_size": str(pack),
    }
    for k in (
        "vegan",
        "vegetarian",
        "halal",
        "organic",
        "gluten_free",
        "lactose_free",
        "sugar_free",
    ):
        if k in attrs and isinstance(attrs[k], bool):
            facets[k] = str(attrs[k]).lower()
    if "halal" in flags:
        facets["halal"] = "true"
    for k in ("country_of_origin", "country_origin", "CountryOfOrigin"):
        if attrs.get(k):
            facets["country_of_origin"] = str(attrs[k])
            break
    bullets = [
        str(attrs[k])
        for k in sorted(attrs)
        if k.startswith("bullet_point_") and attrs[k]
    ]
    stock = product.get("stock")
    stock = (
        int(stock)
        if isinstance(stock, (int, float, str)) and str(stock).isdigit()
        else None
    )
    return {
        "product_id": f"lulu_{source_id}",
        "product_name": name,
        "category": category,
        "brand": facets["brand"],
        "price_aed": str(price.quantize(Decimal("0.01"))),
        "dietary_flags": ",".join(flags),
        "stock_quantity": stock or 0,
        "source_stock_quantity": stock,
        "source_available": product.get("in_stock"),
        "source_id": source_id,
        "source_sku": str(product.get("sku", "")),
        "source_url": safe_url(
            product["absolute_url"]
            if product["absolute_url"].startswith("/en-ae/")
            else "/en-ae" + product["absolute_url"]
        ),
        "retailer": "LuLu UAE",
        "currency": "AED",
        "price_captured_at": captured_at,
        "image_url": images[0],
        "images": images,
        "description": "\n".join(bullets),
        "attributes": {k: v for k, v in facets.items() if v != ""},
        "source_attributes": attrs,
        "unit_type": str(
            product.get("unit_type", (parent or {}).get("unit_type", "qty"))
        ),
        "source_listing_url": path,
        "source_category": str(attrs.get("lulu_product_type", "")),
        "inventory_origin": "retailer_snapshot",
        "pack_variant": parent is not None,
    }


def products_from_listing(data: dict, path: str):
    captured = datetime.now(UTC).isoformat()
    for p in data["products"]:
        row = normalize(p, path, captured)
        if row:
            yield row
        for group in p.get("extra_data", {}).get("variants", []):
            for option in group.get("options", []):
                variant = option.get("product", {})
                if variant.get("pk") == p.get("pk"):
                    continue
                row = normalize(variant, path, captured, parent=p)
                if row:
                    yield row
