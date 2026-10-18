from types import SimpleNamespace

import pytest

from tools.shared.dietary import matches_diet


def product(**changes):
    return {
        "product_id": "rice",
        "product_name": "Daawat Chef's Secretz Light XXXL Basmati Rice 5 kg",
        "category": "grains",
        "dietary_flags": "",
        **changes,
    }


@pytest.mark.parametrize(
    "category",
    ["grains", "vegetables", "fruits", "dairy", "beverages", "snacks", "condiments"],
)
def test_halal_preference_does_not_require_labels_for_nonmeat(category):
    p = product(category=category)
    assert matches_diet(p, "halal")
    assert p["dietary_flags"] == ""


@pytest.mark.parametrize("flags", ["", "vegetarian", "non_halal", "halal,non_halal"])
def test_meat_still_requires_halal_label(flags):
    assert not matches_diet(
        product(category="halal_meat", dietary_flags=flags), "halal"
    )


def test_halal_meat_and_other_dietary_preferences():
    p = product(category="halal_meat", dietary_flags="halal")
    assert matches_diet(p, "halal")
    assert not matches_diet(p, "vegan")
    assert not matches_diet(p, "vegetarian")
    assert matches_diet(product(dietary_flags="vegan"), "vegan")
    assert not matches_diet(product(), "vegan")


def test_cart_accepts_reported_rice_but_checks_meat(monkeypatch):
    import tools.shared.pricing as pricing

    p = product(price_aed=42.5, stock_quantity=20, aisle_ref="B1")
    monkeypatch.setattr(
        pricing,
        "get_alloydb",
        lambda: SimpleNamespace(get_product_at_store=lambda *args: p),
    )
    result = pricing.canonical_items(
        [{"product_id": "rice", "quantity": 1}], "store", "halal"
    )
    assert result["total_aed"] == 42.5
    p.update(product_name="Chicken Breast", category="halal_meat")
    result = pricing.canonical_items(
        [{"product_id": "rice", "quantity": 1}], "store", "halal"
    )
    assert "no verified halal meat label" in str(result)


def test_halal_catalog_filter_keeps_nonmeat():
    from tools.catalog.service import filters

    where, _ = filters("store", "all", "", None, None, False, {"halal": ["true"]})
    assert "category<>'halal_meat'" in where
    assert "string_to_array(dietary_flags" in where


@pytest.mark.parametrize(
    "name",
    ["555 Tuna Flakes In Oil 155 g", "Fresh Salmon Fillet", "Sardines in Tomato Sauce"],
)
def test_seafood_does_not_require_slaughter_label(name):
    from tools.shared.dietary import protein_type

    p = product(product_name=name, category="halal_meat")
    assert protein_type(p) == "seafood"
    assert matches_diet(p, "halal")
    assert not matches_diet(p, "vegan")
    assert p["dietary_flags"] == ""


def test_seafood_name_cannot_hide_land_meat():
    p = product(product_name="Fish and Chicken Dumplings", category="halal_meat")
    assert not matches_diet(p, "halal")
    p = product(
        product_name="Tuna Salad", category="halal_meat", ingredients="Tuna, ham"
    )
    assert not matches_diet(p, "halal")
