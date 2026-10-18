# ARC data model

Updated October 18, 2026 · Specification 1.1

## 1. Storage modes

`USE_MOCK=true` selects the working local implementations. With paths configured,
operational data and incidents persist in **two different SQLite files**. Without
paths, adapters use isolated process memory for tests. The Google `Real*` adapters
remain unimplemented; the SQL files describe a future managed-database mapping.

| Configuration | Contents | Launcher default |
|---|---|---|
| ARC_STATE_DB | Inventory, customers, promotions, orders, POs, sessions, decisions | data/local/operations.sqlite |
| ARC_BRIDGE_DB | Session incidents and substitution-gap counters | data/local/incidents.sqlite |

If only `ARC_BRIDGE_DB` is set, operational storage defaults to that path plus
`.state`. Equal resolved paths are rejected. The launcher sets both explicitly.

## 2. Local physical schema

Operational database:

```sql
CREATE TABLE arc_state (
    id INTEGER PRIMARY KEY CHECK(id=1),
    payload TEXT NOT NULL
);
```

The JSON payload contains `inventory` (list of store/product rows), `customers`,
`promotions`, `orders`, `purchase_orders`, `sessions` and `decisions`. This snapshot
layout serializes operational writes; it is not a normalized relational schema
or a scalable multi-instance database. Replenishment schedules are loaded from
seed data rather than persisted in the snapshot.

Incident database:

```sql
CREATE TABLE arc_incidents (
    session_id TEXT PRIMARY KEY,
    payload TEXT
);
CREATE TABLE arc_sub_gaps (
    product_id TEXT,
    store_id TEXT,
    n INTEGER,
    PRIMARY KEY(product_id, store_id)
);
```

Both databases enable WAL. Operational writes use `BEGIN IMMEDIATE`; incident
upserts are independently committed. See [ARCHITECTURE.md](ARCHITECTURE.md) for the
cross-store atomicity limitation and intended outbox design.

## 3. Operational records

### Inventory

A row is identified by `(product_id, store_id)` and includes product name,
category, brand, base price, comma-separated dietary flags, aisle, stock quantity,
reorder threshold, supplier, perishability, optional expiry date and discount fields.
The effective price uses `discounted_price_aed` only when `discount_active` is true.

Discount approval is store-specific and recalculates the discounted price from
the approved percentage. Transfer preserves the source's reorder threshold and
increments the destination in the same transaction. Checkout consolidates duplicate
product lines before checking and decrementing stock.

Synthetic perishable expiry offsets are applied when a fresh operational store is
created, relative to the current UAE business date. Persisted inventory continues
to age naturally; opening an existing store does not reset expiry dates. The Laban
seed discount is initially inactive.

### Orders

| Field | Meaning |
|---|---|
| order_id | Generated local order identifier |
| customer_id, store_id | Order ownership and inventory scope |
| items | Canonical product names, quantities, current prices and basket flags |
| total_aed, promotion_id | Revalidated quoted total and eligible promotion |
| idempotency_key | Hash of customer/store/session-or-legacy inputs and basket |
| status | confirmed for successful local checkout |
| created_at | UAE-aware ISO timestamp |
| delivery_start_iso, estimated_delivery_window | Future local delivery estimate; not a logistics booking |

Session-based checkout keys persist without the legacy timeout. Calls without a
session key use a 60-second duplicate window. Stock changes, usage counters, order
and session snapshot writes participate in the operational transaction. No payment
record or payment-provider execution is implemented.

### Shopper sessions

`session_id` is a UUID string. Each session includes customer/store binding,
dietary preference, budget, household size, persistent exclusions, current cart,
quote ID, original requested product IDs, unavailable products, substitution offers,
accepted substitutions, demand signals, logging status and optional order/closed state.

The quote ID changes when the basket is repriced. A shopper must review a changed
basket or changed price before confirming. The active browser cart can contain
unquoted edits; those edits are not authoritative order data. A confirmed receipt
is cached in browser session storage for refresh; there is no order-history API.

### Purchase orders

Records include PO ID, product/store, quantity, urgency, justification, optional
supplier and illustrative impact/evidence fields, human-approval requirement,
creator, creation time, status and optional decision time. Status is pending,
approved or rejected. Deduplication reuses any of those states for the same
product/store within 24 hours. Newer cycles can create a new proposal.

### Manager decisions

| Family | Key | Persisted content |
|---|---|---|
| Demand | demand:{store}:{product}:{business_date} | Selected action, quantity, baseline outcome counts, evidence session IDs, execution label, decision time; optional source store or PO ID |
| Discount | discount:{store}:{product}:{expiry_date} | approved/rejected, percentage, product/store, action=discount and decision time |

Demand actions are transfer, replenish or defer. Repeated identical decisions
return the existing record. Conflicting decisions are rejected. Replenishment
records a drafted PO; the manager must review that PO separately.

## 4. Incident records

The bridge maintains **one evolving row per session**, not a row per utterance.
An upsert preserves the first timestamp while replacing the latest session state.
The returned logging-operation timestamp need not be that preserved event time.

| Field | Meaning |
|---|---|
| session_id, customer_id, store_id | Session UUID and demo identities |
| timestamp | First persisted session timestamp |
| requested_items | Explicitly requested original product IDs |
| items_ordered | Canonical lines when an order was placed |
| items_unavailable | Requested originals unavailable during the session |
| substitutions_offered | Original/alternative IDs and acceptance flags |
| demand_signals | Structured product-level outcome evidence |
| session_status | active, completed or abandoned |
| order_placed | Whether this session has a confirmed local order |
| promotion_id, promotion_saving_aed | Applied quote promotion information |
| cart_total_aed, budget_aed | Basket and constraint context |
| session_sentiment | Existing neutral/positive/negative contract field; local orchestration uses neutral |
| abandonment_reason | Reason recorded when the session closes without an order |
| data_origin | synthetic_seed for historical demo incidents; absent on local customer rows |

Active unfinished sessions are not counted as abandonment by the current writer.
Legacy rows lacking `session_status` still use their `order_placed` flag for the
older stockout aggregation. No idle-timeout abandonment detection is implemented.

### Demand signal

```json
{
  "product_id": "rice_brown_500g",
  "product_name": "Brown Rice 500g",
  "outcome": "compromise",
  "substitute_product_id": "rice_basmati_5kg",
  "evidence": "Okay this time; I still prefer the original.",
  "evidence_source": "customer_statement",
  "certainty": "explicit"
}
```

Outcomes are satisfied, compromise, rejected, abandoned, fulfilled or unknown.
Explicit unresolved counts sum compromise/rejected/abandoned. Unknown is excluded.
`fulfilled` is created from a confirmed order containing the requested original
and uses `evidence_source=order_record`, `certainty=observed`. Synthetic statements
use a synthetic source label. `certainty` is not a calibrated probability.

The Python boundary is documented by `DemandSignal` in `tools/shared/models.py`.
The current logger validates required product/outcome values; it does not enforce
that entire Pydantic model on every stored legacy row. One current signal per
product/session is used in aggregation.

## 5. Aggregates and observation

Stockout patterns deduplicate unavailable products within each session, filter
by store/window and attach sample sessions, first/last timestamps, peak-hour and
substitution-acceptance evidence. Default minimum: five incidents over 48 hours.

Demand insights separately aggregate the six outcome categories, attach customer
statements and source labels, compare actions and include the persisted decision.
At least three explicit unresolved signals are needed for stock-changing options.
Post-decision monitoring compares a stored baseline to sessions whose preserved
first timestamp is later than the decision. It is descriptive, not causal, and
retains the historical evidence rather than deleting it after an intervention.

## 6. Future managed-database mapping

- [data/schema/alloydb_schema.sql](data/schema/alloydb_schema.sql): original planned
  normalized operational tables. It does not yet cover the complete local session,
  quote, decision and outbox design. Production migration work remains.
- [data/schema/bigquery_schema.sql](data/schema/bigquery_schema.sql): planned incident
  JSON columns now include demand_signals, requested_items and session_status.
  `CREATE TABLE IF NOT EXISTS` does not migrate an existing table; explicit schema
  migrations are needed before a real adapter can use these fields.
- `data/seed/01_stores_suppliers_customers.sql`, `02_inventory.sql`,
  `03_promotions.sql`, `04_replenishment.sql` are cloud-oriented fixtures. Current
  local adapters use `tools/shared/mock_inventory.py` and synthetic incident seeds.
- SQL forecast definitions are planned assets, not evidence that BigQuery ML is
  trained or called by the prototype.
