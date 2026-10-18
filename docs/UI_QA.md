# Demo UI verification — 18 October 2026

Branch: `fix/branded-login-dashboard`.

Automated verification: 182 Python tests; 12 Node tests (`npm test` in `frontend/aria-app`); Next.js production build and TypeScript checks pass.

| Area | Verified coverage |
|---|---|
| Authentication | Invalid credentials, signed/expiring cookies, rotation, customer identity binding, safe redirects, origin checks, manager login and avatar/sidebar logout |
| Store navigation | Cart and orders destinations, functional Offers selection, category and dietary/stock filters, attribute selection and clear filters |
| Catalog | Product links/add, unavailable state, pagination, sort, page size, approved-offer requests |
| Cart and orders | Increase/decrease/remove, explicit review then confirmation contract, quote ID, order refresh/pagination, durable checkout and idempotency |
| PULSE | All six pages, store/period changes, refresh, alert drill-in, approval/rejection, customer activity and persistent history |
| Manager loop | Transfers, discount price propagation, one-time PO receipt, unchanged stock on rejection, rollback on failure, same and next shopper availability |

Visual checks covered the branded login pages and PULSE overview chart rendering. This is not an exhaustive audit across browsers, mobile sizes, screen readers or every built-in Streamlit chart toolbar control.

A real Google PostgreSQL transaction verified restock persistence and retry idempotency, then rolled back to leave stock/history unchanged. `scripts/smoke_cloud.py` verifies deployed form authentication, customer scoping, catalog, weekly cart, explicit checkout, order history, private API protection and Google analysis. It removes its own QA records and restores checkout stock.

Hosted smoke test passed on release `demo-ux-loop-20261018-v4`: form login/customer scoping, 4,145-product catalog, weekly cart (20 lines, AED 127.62), explicit rejection evidence, confirmed checkout/history/idempotency, and Google analysis. Temporary QA records were removed and stock restored. Both frontend URLs serve the new release; hosted PULSE login was visually checked.
