"""SQL pagination, product detail and data-driven facets; never fetch the whole catalog."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text

from tools.shared.database import get_engine

FACET_KEYS = (
    "brand",
    "product_type",
    "pack_size",
    "country_of_origin",
    "organic",
    "vegan",
    "vegetarian",
    "halal",
    "gluten_free",
    "lactose_free",
    "sugar_free",
)
LIST_COLUMNS = "product_id,product_name,category,brand,price_aed,dietary_flags,store_id,aisle_ref,stock_quantity,reorder_threshold,supplier_id,is_perishable,expiry_date,discount_active,discount_pct,image_url,attributes,currency,unit_type,source_category,source_attributes->>'ingredients' AS ingredients"
PRICE = "CASE WHEN discount_active THEN price_aed*(1-COALESCE(discount_pct,0)/100) ELSE price_aed END"


def serialize(row):
    data = dict(row)
    for k, v in data.items():
        if isinstance(v, Decimal):
            data[k] = float(v)
        elif isinstance(v, (datetime, date)):
            data[k] = v.isoformat()
    data["discounted_price_aed"] = round(
        data["price_aed"] * (1 - (data.get("discount_pct") or 0) / 100), 2
    )
    return data


def filters(store_id, category, q, min_price, max_price, in_stock, attributes):
    where = ["store_id=:store"]
    params = {"store": store_id}
    if category and category != "all":
        where.append("category=:category")
        params["category"] = category
    if q:
        where.append("(product_name || ' ' || COALESCE(brand,'')) ILIKE :q ESCAPE '\\'")
        params["q"] = (
            "%" + q.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_") + "%"
        )
    if min_price is not None:
        where.append(f"{PRICE}>=CAST(:minimum AS NUMERIC)")
        params["minimum"] = min_price
    if max_price is not None:
        where.append(f"{PRICE}<=CAST(:maximum AS NUMERIC)")
        params["maximum"] = max_price
    if in_stock:
        where.append("stock_quantity>0")
    for index, (key, values) in enumerate(attributes.items()):
        if key not in FACET_KEYS:
            raise ValueError("Unsupported facet")
        if (
            not isinstance(values, list)
            or not 1 <= len(values) <= 30
            or any(not isinstance(v, str) or len(v) > 200 for v in values)
        ):
            raise ValueError("Invalid facet values")
        choices = []
        for n, value in enumerate(values):
            token = f"facet_{index}_{n}"
            if key == "brand":
                choices.append(f"{key}=:{token}")
                params[token] = value
            else:
                if key == "halal" and value == "true":
                    choices.append("(category<>'halal_meat' OR attributes->>'protein_type'='seafood' OR 'halal'=ANY(string_to_array(dietary_flags, ',')))")
                else:
                    choices.append(f"attributes @> CAST(:{token} AS JSONB)")
                params[token] = json.dumps({key: value})
        where.append("(" + " OR ".join(choices) + ")")
    return " AND ".join(where), params


def list_products(
    *,
    store_id,
    category="all",
    q="",
    page=1,
    page_size=24,
    sort="name",
    min_price=None,
    max_price=None,
    in_stock=False,
    attributes=None,
):
    order = {
        "name": "product_name,product_id",
        "price_asc": f"{PRICE},product_id",
        "price_desc": f"{PRICE} DESC,product_id",
        "newest": "price_captured_at DESC NULLS LAST,product_id",
    }
    if sort not in order:
        raise ValueError("Unsupported sort")
    if not 1 <= page_size <= 96 or page < 1:
        raise ValueError("Invalid page")
    where, params = filters(
        store_id, category, q, min_price, max_price, in_stock, attributes or {}
    )
    with get_engine().connect() as conn:
        summary = (
            conn.execute(
                text(
                    f"SELECT COUNT(*) total,MIN({PRICE}) minimum,MAX({PRICE}) maximum FROM inventory WHERE {where}"
                ),
                params,
            )
            .mappings()
            .one()
        )
        total = int(summary["total"])
        pages = max(1, (total + page_size - 1) // page_size)
        rows = conn.execute(
            text(
                f"SELECT {LIST_COLUMNS} FROM inventory WHERE {where} ORDER BY {order[sort]} LIMIT :limit OFFSET :offset"
            ),
            {**params, "limit": page_size, "offset": (page - 1) * page_size},
        ).mappings()
        items = [serialize(r) for r in rows]
        # Ignore a facet's own selection so additional choices remain available.
        buckets, facet_params = [], {}
        for index, key in enumerate(FACET_KEYS):
            facet_where, bindings = filters(
                store_id,
                category,
                q,
                min_price,
                max_price,
                in_stock,
                {k: v for k, v in (attributes or {}).items() if k != key},
            )
            facet_where = re.sub(
                r":([a-z_0-9]+)\b", lambda m: f":f{index}_{m[1]}", facet_where
            )
            facet_params.update({f"f{index}_{k}": v for k, v in bindings.items()})
            expression = "brand" if key == "brand" else f"attributes->>'{key}'"
            buckets.append(
                f"SELECT '{key}' key, {expression} value, COUNT(*) count FROM inventory WHERE {facet_where} GROUP BY {expression}"
            )
        sql = (
            "WITH buckets AS ("
            + " UNION ALL ".join(buckets)
            + """),
            ranked AS (SELECT *,ROW_NUMBER() OVER(PARTITION BY key ORDER BY count DESC,value) n FROM buckets WHERE value IS NOT NULL AND value<>'')
            SELECT key,value,count FROM ranked WHERE n<=250 ORDER BY key,count DESC,value"""
        )
        facets = {}
        for row in conn.execute(text(sql), facet_params).mappings():
            if row["value"] != "":
                facets.setdefault(row["key"], []).append(
                    {"value": row["value"], "count": int(row["count"])}
                )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": pages,
        "facets": facets,
        "price_range": {
            "min": float(summary["minimum"] or 0),
            "max": float(summary["maximum"] or 0),
        },
    }


def product_detail(product_id, store_id):
    with get_engine().connect() as conn:
        row = (
            conn.execute(
                text(
                    f"SELECT {LIST_COLUMNS},images,description FROM inventory WHERE product_id=:pid AND store_id=:store"
                ),
                {"pid": product_id, "store": store_id},
            )
            .mappings()
            .first()
        )
        return serialize(row) if row else None


def planner_candidates(store_id, message, product_ids):
    """Bound planner context while retaining basket items and category diversity."""
    from tools.shared.settings import settings

    if settings.use_mock:
        from tools.shared.alloydb_client import get_alloydb

        return get_alloydb().list_inventory(store_id)
    stop = {"weekly", "groceries", "grocery", "family", "people", "include", "including", "please", "need", "want", "halal", "aed", "for", "with", "the", "and", "cart", "basket"}
    words = [w for w in re.findall(r"[a-zA-Z]{3,}", message.lower()) if w not in stop][:40]
    query = " | ".join(words)
    with get_engine().connect() as conn:
        rows = conn.execute(
            text(f"""
            WITH typed AS (
                SELECT product_id,category,stock_quantity,price_aed,
                    ROW_NUMBER() OVER(PARTITION BY category,COALESCE(attributes->>'product_type',category)
                        ORDER BY stock_quantity>0 DESC,price_aed,product_id) subtype_position
                FROM inventory WHERE store_id=:store
            ), ranked AS (
                SELECT product_id,ROW_NUMBER() OVER(PARTITION BY category
                    ORDER BY stock_quantity>0 DESC,subtype_position,price_aed,product_id) position FROM typed
            ), candidates AS (
                SELECT product_id FROM ranked WHERE position<=8
                UNION SELECT product_id FROM inventory WHERE store_id=:store AND product_id=ANY(:ids)
                UNION (SELECT product_id FROM inventory WHERE store_id=:store
                    AND to_tsvector('english',product_name) @@ to_tsquery('english',:query)
                    ORDER BY stock_quantity>0 DESC,ts_rank(to_tsvector('english',product_name),to_tsquery('english',:query)) DESC,product_id LIMIT 48)
            ) SELECT {LIST_COLUMNS} FROM inventory WHERE store_id=:store
                AND product_id IN (SELECT product_id FROM candidates)
            ORDER BY product_id
        """),
            {"store": store_id, "query": query, "ids": list(product_ids)},
        ).mappings()
        return [serialize(row) for row in rows]
