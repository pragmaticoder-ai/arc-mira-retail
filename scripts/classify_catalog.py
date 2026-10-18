#!/usr/bin/env python3
"""Refresh protein classification without modifying prices, stock or certificates."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text  # noqa: E402

from tools.shared.database import get_engine  # noqa: E402
from tools.shared.dietary import protein_type  # noqa: E402
from tools.shared.settings import settings  # noqa: E402


def main():
    if settings.use_mock:
        raise SystemExit("USE_MOCK=false is required")
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(724031)"))
        rows = conn.execute(
            text(
                "SELECT product_id,product_name,category,attributes,source_category,source_attributes->>'ingredients' AS ingredients FROM inventory WHERE category='halal_meat'"
            )
        ).mappings()
        groups = defaultdict(set)
        for row in rows:
            groups[protein_type(dict(row))].add(row["product_id"])
        for kind, ids in groups.items():
            conn.execute(
                text("""UPDATE inventory SET attributes=jsonb_set(attributes,'{protein_type}',CAST(:kind AS JSONB)),updated_at=NOW()
                WHERE category='halal_meat' AND product_id=ANY(:ids)
                AND attributes->>'protein_type' IS DISTINCT FROM :plain"""),
                {"kind": json.dumps(kind), "plain": kind, "ids": list(ids)},
            )
    print(json.dumps({k: len(v) for k, v in groups.items()}, indent=2))


if __name__ == "__main__":
    main()
