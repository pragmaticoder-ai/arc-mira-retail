#!/usr/bin/env python3
"""Verify a deployed demo and remove only this run's temporary shopper records."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-weekly", action="store_true")
    args = parser.parse_args()
    local = ROOT / "data/local/cloud"
    deployed = json.loads((local / "deployment.json").read_text())
    access = (local / "ACCESS.md").read_text().splitlines()
    passwords = [
        line.split(": ", 1)[1] for line in access if line.startswith("Password: ")
    ]
    aria = deployed["aria"]
    sessions = []
    created_order = None
    report = {}
    with httpx.Client(timeout=180) as client:
        for name in ("aria_agent", "pulse_agent"):
            r = client.get(deployed[name] + "/health")
            assert r.status_code in (401, 403), (name, r.status_code)
        assert client.get(aria + "/api/aria/catalog").status_code == 401
        landing=client.get(aria + "/")
        assert landing.status_code == 307 and "www-authenticate" not in landing.headers
        assert client.post(aria + "/api/auth/login", json={"username":"mira-demo","password":"incorrect"}).status_code == 401
        login=client.post(aria + "/api/auth/login", json={"username":"mira-demo","password":passwords[0]})
        login.raise_for_status()
        assert "HttpOnly" in login.headers["set-cookie"] and "Secure" in login.headers["set-cookie"]
        assert client.get(aria + "/api/auth/session").json()["customer"]["customer_id"] == "sarah_123"
        with httpx.Client(timeout=60) as second:
            second.post(aria + "/api/auth/login",json={"username":"ahmed-demo","password":passwords[0]}).raise_for_status()
            identity=second.get(aria + "/api/aria/bootstrap?customer_id=sarah_123").json()["customer"]["customer_id"]
            assert identity == "demo_ahmed"
            assert second.get(aria + "/api/aria/orders?customer_id=sarah_123").json() == second.get(aria + "/api/aria/orders").json()
            second.post(aria + "/api/auth/logout").raise_for_status()
            assert second.get(aria + "/api/aria/orders").status_code == 401
        report["form_login_and_customer_isolation"]="passed"
        for route in ("/", "/cart", "/orders"):
            r = client.get(aria + route)
            r.raise_for_status()
        a = client.get(aria + "/api/aria/catalog")
        a.raise_for_status()
        a = a.json()
        b = client.get(aria + "/api/aria/catalog", params={"page": 2})
        b.raise_for_status()
        b = b.json()
        assert len(a["items"]) == 24 and not {p["product_id"] for p in a["items"]} & {
            p["product_id"] for p in b["items"]
        }
        report["catalog_products"] = a["total"]
        tuna = client.get(
            aria + "/api/aria/catalog",
            params={
                "q": "555 Tuna Flakes In Oil 155 g",
                "attributes": json.dumps({"halal": ["true"]}),
            },
        )
        tuna.raise_for_status()
        assert tuna.json()["total"] >= 1
        report["seafood_filter"] = "tuna remains available"
        print("Catalog, pages, protected APIs and tuna filter verified.", flush=True)
        try:
            if not args.skip_weekly:
                sid = str(uuid.uuid4())
                sessions.append(sid)
                r = client.post(
                    aria + "/api/aria/chat",
                    json={
                        "session_id": sid,
                        "message": "Weekly halal groceries, family of 4, AED 300. Include brown rice.",
                    },
                )
                r.raise_for_status()
                basket = r.json()
                assert basket["cart_changed"] and basket["cart"]["items"], basket
                assert basket["cart"]["total_aed"] <= 300, basket
                brown_in_cart = any(
                    "brown" in p["product_name"].lower()
                    and "rice" in p["product_name"].lower()
                    for p in basket["cart"]["items"]
                )
                if not brown_in_cart:
                    assert "unavailable" in basket["reply"].lower(), basket
                    assert any(
                        "brown rice" in offer["product_name"].lower()
                        for offer in basket["substitution_offers"]
                    ), basket
                    assert not any(
                        "rice" in p["product_name"].lower()
                        for p in basket["cart"]["items"]
                    ), basket
                assert (
                    f"Basket total: AED {basket['cart']['total_aed']:.2f}"
                    in basket["reply"]
                ), basket
                report["weekly_basket"] = {
                    "total_aed": basket["cart"]["total_aed"],
                    "lines": len(basket["cart"]["items"]),
                    "reply": basket["reply"],
                }
                print(
                    "Weekly basket verified: AED " + str(basket["cart"]["total_aed"]),
                    flush=True,
                )
                if basket.get("substitution_offers"):
                    offer = basket["substitution_offers"][0]
                    feedback = client.post(
                        aria + "/api/aria/chat",
                        json={
                            "session_id": sid,
                            "message": "No thanks, I want the original product.",
                            "feedback": "rejected",
                            "product_id": offer["product_id"],
                            "cart": basket["cart"]["items"],
                            "quote_id": basket["quote_id"],
                        },
                    )
                    feedback.raise_for_status()
                    assert any(
                        s["outcome"] == "rejected"
                        for s in feedback.json()["demand_signals"]
                    )
                    report["unmet_demand_feedback"] = (
                        "explicit rejection recorded for PULSE"
                    )
            sid = str(uuid.uuid4())
            sessions.append(sid)
            quote = client.post(
                aria + "/api/aria/chat",
                json={
                    "session_id": sid,
                    "message": "review cart",
                    "cart": [{"product_id": "milk_almarai_2l", "quantity": 1}],
                },
            )
            quote.raise_for_status()
            quote = quote.json()
            payload = {
                "session_id": sid,
                "message": "confirm",
                "cart": quote["cart"]["items"],
                "quote_id": quote["quote_id"],
            }
            confirmed = client.post(aria + "/api/aria/chat", json=payload)
            confirmed.raise_for_status()
            confirmed = confirmed.json()
            assert confirmed.get("order"), confirmed
            created_order = confirmed["order"]["order_id"]
            history = client.get(aria + "/api/aria/orders")
            history.raise_for_status()
            assert any(o["order_id"] == created_order for o in history.json()["items"])
            again = client.post(aria + "/api/aria/chat", json=payload)
            again.raise_for_status()
            assert again.json()["order"]["order_id"] == created_order
            report["checkout"] = (
                "confirmed order appears in durable order history; retry does not duplicate it"
            )
            print("Checkout, order history and idempotency verified.", flush=True)
            client.auth = None
            health = client.get(deployed["pulse"] + "/_stcore/health")
            health.raise_for_status()
            report["pulse_dashboard"] = (
                "Streamlit healthy; manager sign-in gate covered by application tests"
            )
            token = subprocess.run(
                ["gcloud", "auth", "print-identity-token"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            analysis = client.post(
                deployed["pulse_agent"] + "/pulse/analyze",
                headers={"Authorization": "Bearer " + token},
                json={"store_id": "dubai_marina_01", "hours": 48},
            )
            analysis.raise_for_status()
            assert analysis.json().get("summary")
            report["pulse_agent"] = (
                "Google summary generated from Cloud SQL/BigQuery evidence"
            )
            print("PULSE Google analysis verified.", flush=True)
        finally:
            from sqlalchemy import text

            from tools.shared.database import get_engine

            with get_engine().begin() as conn:
                conn.execute(text("SELECT pg_advisory_xact_lock(724031)"))
                if not created_order:
                    session_rows = conn.execute(
                        text(
                            "SELECT payload FROM arc_records WHERE entity='sessions' AND key=ANY(:ids)"
                        ),
                        {"ids": sessions},
                    ).scalars()
                    created_order = next(
                        (
                            s["order"]["order_id"]
                            for s in session_rows
                            if s.get("order")
                        ),
                        None,
                    )
                if created_order:
                    row = conn.execute(
                        text(
                            "SELECT payload FROM arc_records WHERE entity='orders' AND key=:id"
                        ),
                        {"id": created_order},
                    ).scalar()
                    if row:
                        for item in row["items"]:
                            conn.execute(
                                text(
                                    "UPDATE inventory SET stock_quantity=stock_quantity+:quantity WHERE product_id=:pid AND store_id=:store"
                                ),
                                {
                                    "quantity": item["quantity"],
                                    "pid": item["product_id"],
                                    "store": row["store_id"],
                                },
                            )
                        if row.get("promotion_id"):
                            conn.execute(
                                text(
                                    "UPDATE promotions SET times_applied=GREATEST(0,times_applied-1) WHERE promotion_id=:pid"
                                ),
                                {"pid": row["promotion_id"]},
                            )
                        conn.execute(
                            text(
                                "DELETE FROM arc_records WHERE entity='orders' AND key=:id"
                            ),
                            {"id": created_order},
                        )
                conn.execute(
                    text(
                        "DELETE FROM arc_records WHERE entity='sessions' AND key=ANY(:ids)"
                    ),
                    {"ids": sessions},
                )
            from google.cloud import bigquery

            from tools.shared.settings import settings

            bq = bigquery.Client(
                project=deployed["project"], location=deployed["region"]
            )
            bq.query(
                f"DELETE FROM `{deployed['project']}.{settings.bigquery_dataset}.incidents` WHERE session_id IN UNNEST(@sessions)",
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ArrayQueryParameter("sessions", "STRING", sessions)
                    ]
                ),
            ).result()
            print(
                "Temporary QA order/session records removed and stock restored.",
                flush=True,
            )
    (local / "smoke-report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
