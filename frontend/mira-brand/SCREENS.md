# ARC screen inventory — current implementation

Updated October 18, 2026. [BRAND.md](BRAND.md) supplies MIRA visual tokens. The static HTML design is a visual reference; live behavior follows implemented contracts.

## ARIA

- `/login`: branded customer picker and password form; remembers a signed HttpOnly session. Five fictional customer profiles use one shared demo password, with no signup requirement.
- `/`: store selector, search, functional approved Offers filter, categories and attribute facets, sorting, paginated products, product links and ARIA conversation.
- `/products/[productId]`: images, attributes, stock, current price, bounded add-to-basket button, basket navigation and account menu.
- `/cart`: quantities, removal, product links, ARIA, quote review and explicit confirmation. Stock and prices are revalidated by the backend.
- `/orders`: current customer's persisted orders, refresh and pagination.
- `/order/confirmed`: actual stored order and links to order history or a fresh shopping session.

The avatar menu exposes My orders, Switch customer and Sign out. Customer identity comes from the signed cookie, overriding client-supplied IDs. Baskets and conversation storage are scoped by customer; orders are filtered by authenticated identity. No browser Basic Auth popup is used.

## PULSE

Manager login uses the dark slate background, MIRA logo, amber PULSE badge, Manager ID/password, store picker and Access dashboard control. Sidebar controls store, period, page, refresh and sign out.

Overview has a green store banner, summary cards, recorded hourly request activity, demand-outcome bars, separately labeled modeled exposure, recent decisions and alert previews. Empty charts explain which evidence is missing. Synthetic sessions are labeled and estimates are never presented as measured recovered revenue.

Unmet demand exposes evidence, alternative outcomes, transfer/replenish/defer choices and after-decision observations. Stockout alerts drill into evidence and PO decisions. Perishables provide stock, expiry, exposure and discount decisions. Customer activity separates profiles, sessions, baskets and orders. Action history retains completed, approved, rejected and monitoring decisions, with a status filter.

Approvals persist before confirmation. Transfers and discounts update shared inventory/prices. PO approval explicitly simulates receipt in this demo and adds inventory only once. Rejected actions leave inventory/prices unchanged. History remains visible when active alerts disappear. New ARIA interactions use the shared updates; checkout revalidates older quotes.
