"""Catalog import rejects invented prices and dietary/stock claims."""

from tools.catalog.service import filters, serialize
from tools.catalog.sources import category_for, normalize


def source_product(**changes):
    return {
        "pk": 123,
        "name": "Basmati Rice 1 kg",
        "price": "12.50",
        "currency_type": "aed",
        "absolute_url": "/rice/p/123/",
        "productimage_set": [{"image": "https://example.com/rice.jpg"}],
        "attributes": {"lulu_product_type": "Rice", "brand": "Example"},
        **changes,
    }


def test_product_requires_real_price_and_image():
    for price in ("0", "-1", "NaN", "Infinity", "invalid"):
        assert normalize(source_product(price=price), "", "2026-10-18") is None
    assert normalize(source_product(productimage_set=[]), "", "2026-10-18") is None
    assert normalize(source_product(currency_type="usd"), "", "2026-10-18") is None


def test_unknown_stock_and_diet_remain_unknown():
    row = normalize(source_product(), "", "2026-10-18")
    assert row["source_stock_quantity"] is None
    assert row["source_available"] is None
    assert row["dietary_flags"] == ""
    assert "halal" not in row["attributes"]
    assert row["attributes"]["pack_size"] == "1 kg"


def test_variant_uses_own_price_pack_and_unknown_stock():
    parent = source_product(
        stock=7, attributes={"content": "1 kg", "lulu_product_type": "Rice"}
    )
    child = source_product(
        pk=124, name="Basmati Rice 5 kg", price="45.75", attributes={}
    )
    row = normalize(child, "", "2026-10-18", parent)
    assert row["price_aed"] == "45.75"
    assert row["attributes"]["pack_size"] == "5 kg"
    assert row["source_stock_quantity"] is None


def test_category_is_not_a_certification():
    row = normalize(
        source_product(
            name="Chicken Breast", attributes={"lulu_product_type": "Poultry"}
        ),
        "",
        "2026-10-18",
    )
    assert row["category"] == "halal_meat"
    assert "halal" not in row["dietary_flags"]
    assert category_for({"lulu_product_type": "Pasta Sauce"}) == "condiments"
    assert category_for({}, "/fresh-food-fruits-vegetables-fruits/") == "fruits"


def test_filter_values_are_bound_and_retailer_facets_rejected():
    import pytest

    where, params = filters(
        "store", "all", "50%_rice", None, 0, False, {"brand": ["x' OR true --"]}
    )
    assert "x' OR true" not in where
    assert params["maximum"] == 0
    assert params["q"] == r"%50\%\_rice%"
    with pytest.raises(ValueError):
        filters("store", "all", "", None, None, False, {"retailer": ["anything"]})


def test_product_serialization_keeps_numeric_prices():
    from decimal import Decimal

    assert (
        serialize({"price_aed": Decimal("12.50"), "discount_pct": Decimal("10")})[
            "discounted_price_aed"
        ]
        == 11.25
    )
