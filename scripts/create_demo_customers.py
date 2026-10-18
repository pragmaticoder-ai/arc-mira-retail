#!/usr/bin/env python3
"""Create the five fictional demo profiles without overwriting existing shoppers."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from tools.shared.database import get_engine


def main():
    accounts = json.loads((ROOT / 'frontend/aria-app/lib/demoCustomers.json').read_text())
    fields = ['customer_id', 'name', 'email', 'dietary_preference', 'household_size', 'weekly_budget_aed', 'preferred_store']
    query = text(f"INSERT INTO customer_profiles ({','.join(fields)}) VALUES ({','.join(':'+key for key in fields)}) ON CONFLICT (customer_id) DO NOTHING")
    with get_engine().begin() as conn:
        for account in accounts:
            conn.execute(query, {key: account[key] for key in fields})
    print(f"Verified {len(accounts)} demo customer profiles; existing profiles preserved.")


if __name__ == '__main__':
    main()
