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

MIRA requires a verified halal meat label for land-animal meat and poultry.
The legacy `halal_meat` browsing category includes seafood, so the category
alone does not determine whether a slaughter label is required. The importer
classifies `attributes.protein_type` as `land_meat`, `seafood`, or `unknown`;
land-animal ingredients take priority in mixed products. Seafood does not
require a halal slaughter label under this demo's shopping policy. Unknown
meat products retain the label requirement. Existing catalogs can be updated
without changing stock, prices or certifications:

```sh
.venv/bin/python scripts/classify_catalog.py
```

Rice, produce and other non-meat groceries remain available without a halal
label. This rule never adds certification flags to those products.
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

## Cart and orders

The navigation cart opens `/cart`, where shoppers can change quantities, remove
items, review current prices with ARIA, and explicitly confirm a quote. Basket
items and the ARIA session are preserved in browser session storage across
navigation and reloads. Checkout still validates the server quote and reserves
stock atomically; navigation never places an order.

`/orders` reads confirmed order records from the backend, including products,
quantities, totals, store, status and delivery window. `GET /aria/orders` accepts
`customer_id`, optional `store_id`, `page`, and `page_size` (1–50). The storefront
proxy uses its configured demo customer, matching bootstrap. Order history
comes from durable storage rather than the browser confirmation receipt.

Weekly requests use diverse category candidates and prioritize stocked matches.
Planner proposals are validated before business state changes; invalid proposals
receive one bounded correction attempt. Explicit brown-rice requests must include
available matching brown rice, rather than silently substituting white rice.
