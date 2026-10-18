# MIRA demo catalog

The enriched catalog is loaded into the existing MIRA Dubai Marina store
(`dubai_marina_01`). The completed import added 4,096 distinct products,
bringing that store to 4,145 products including its existing items. It includes product photographs, AED prices, pack sizes,
brands, descriptions when available, and explicit product attributes. Other
MIRA stores retain their existing inventory.

The demo displays MIRA branding. Original import records and provenance remain
internal; shopper catalog and detail responses omit retailer names and links.
Retailer own-label text is mapped to MIRA for the fictional demo.

## Import and local use

```sh
# Collect/checkpoint public product data (cached files are gitignored).
.venv/bin/python scripts/scrape_catalog.py
# Apply the additive catalog migration and load the existing MIRA catalog.
.venv/bin/python scripts/import_catalog.py
# Start the local apps against the configured Google resources.
.venv/bin/python scripts/run_local.py --skip-checks
```

Imports deduplicate source SKUs and preserve existing MIRA stock and discounts
on reruns. Price and descriptive metadata refresh from the collected records.
Distinct pack variants keep their own price and image. When a source variant
has no stock quantity, newly imported MIRA demo inventory starts at 20 units;
this is fictional store inventory, not a claim about external availability.

MIRA applies the halal preference to meat products only (the legacy category
key is `halal_meat`). A verified halal meat label is required for that category.
Rice, produce and other non-meat groceries remain available regardless of a
halal label. This rule does not add certification flags to non-meat products.
Vegetarian and vegan preferences continue to use the appropriate product labels.
Missing descriptions are omitted.

## Browsing

`GET /aria/catalog` accepts `store_id`, `category`, `q`, `page`, `page_size`
(1–96), `sort` (`name`, `price_asc`, `price_desc`, `newest`), `min_price`,
`max_price`, `in_stock`, and JSON `attributes` mapping supported facet keys to
lists of values. Responses include items, total pages, price range and facet
counts across the matching catalog. Values within a facet use OR; different
facets use AND. A facet's own selected values do not hide its other choices.

`GET /aria/products/{product_id}?store_id=...` returns product details, available
images and description. The storefront provides pagination, search, price and
attribute filters, sorting, and product detail pages.

The shopping planner retrieves a bounded set of matching products, category
representatives and current basket items instead of sending the full catalog
to Gemini. The server still validates stock, prices and dietary constraints.
