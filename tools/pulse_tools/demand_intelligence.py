"""Turn explicit unmet intent into reviewable actions and descriptive outcomes."""
from __future__ import annotations

from datetime import datetime, timedelta

from tools.shared.alloydb_client import get_alloydb
from tools.shared.bigquery_client import get_bigquery
from tools.shared.clock import now, today
from tools.shared.demand import outcome_counts


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=now().tzinfo)


def demand_insights(store_id: str, hours: int = 48) -> list[dict]:
    if not 1 <= hours <= 168:
        raise ValueError("hours must be 1–168")
    db = get_alloydb()
    incidents = get_bigquery().list_incidents(store_id)
    groups: dict[str, list[dict]] = {}
    for row in incidents:
        if not now() - timedelta(hours=hours) <= _timestamp(row["timestamp"]) <= now():
            continue
        # At most one signal for a product in a session.
        unique = {s["product_id"]: s for s in row.get("demand_signals", [])}
        for pid, item in unique.items():
            groups.setdefault(pid, []).append({**item, "session_id": row["session_id"],
                "timestamp": row["timestamp"], "order_placed": row.get("order_placed", False),
                "data_origin": row.get("data_origin", "customer_session")})
    output = []
    for pid, evidence in groups.items():
        counts = outcome_counts(evidence)
        product = db.get_product_at_store(pid, store_id)
        if not product:
            continue
        key = f"demand:{store_id}:{pid}:{today().isoformat()}"
        decision = db.get_decision(key)
        alternatives = []
        for source in db.list_product_across_stores(pid, exclude_store_id=store_id):
            spare = source["stock_quantity"] - source["reorder_threshold"]
            if spare > 0:
                alternatives.append({"store_id": source["store_id"], "available_above_safety_stock": spare})
        alternatives.sort(key=lambda s: s["available_above_safety_stock"], reverse=True)
        qty = min(max(counts["unresolved"], 1), alternatives[0]["available_above_safety_stock"]) if alternatives else 0
        schedule = db.get_replenishment(store_id, pid)
        choices = [
            {"action": "transfer", "available": bool(alternatives) and counts["unresolved"] >= 3,
             "source_store_id": alternatives[0]["store_id"] if alternatives else None, "quantity": qty,
             "reason": "Uses stock above the source store's reorder threshold. Local transfer simulation; no carrier integration."},
            {"action": "replenish", "available": counts["unresolved"] >= 3,
             "quantity": max(counts["unresolved"], product["reorder_threshold"]),
             "lead_time_days": schedule.get("lead_time_days") if schedule else None,
             "reason": "Creates a purchase-order draft for manager review; no stock is added before delivery."},
            {"action": "defer", "available": True, "quantity": 0,
             "reason": "Keep collecting evidence without changing inventory."},
        ]
        recommended = "transfer" if choices[0]["available"] else "replenish" if counts["unresolved"] >= 3 else "defer"
        after = [e for e in evidence if decision and _timestamp(e["timestamp"]) > _timestamp(decision["decided_at"])]
        post = outcome_counts(after)
        baseline = decision.get("baseline", counts) if decision else counts
        output.append({"product_id": pid, "product_name": product["product_name"], "store_id": store_id,
            "proposal_key": key, "counts": counts, "evidence": evidence,
            "synthetic_sessions": sum(e["data_origin"] == "synthetic_seed" for e in evidence),
            "summary": f"{counts['unresolved']} explicit unmet needs, including {counts['compromise']} temporary compromises. "
                       f"{counts['satisfied']} satisfied substitutions; {counts['unknown']} outcomes need clarification.",
            "recommended_action": recommended, "action_options": choices, "decision": decision,
            "outcome_monitor": {"baseline": baseline, "after": post, "after_sessions": len(after),
                "status": "collecting" if decision else "awaiting_action",
                "note": "Observed session outcomes only. This is not a causal estimate or verified revenue recovery."}})
    return sorted(output, key=lambda x: x["counts"]["unresolved"], reverse=True)


def decide_demand(proposal_key: str, store_id: str, action: str) -> dict:
    db = get_alloydb()
    with db.transaction():
        existing = db.get_decision(proposal_key)
        if existing:
            if existing["store_id"] != store_id or existing["action"] != action:
                raise ValueError("Proposal already decided")
            return existing
        insight = next((i for i in demand_insights(store_id) if i["proposal_key"] == proposal_key), None)
        if insight is None:
            raise ValueError("Proposal expired or not found")
        choice = next((c for c in insight["action_options"] if c["action"] == action and c["available"]), None)
        if choice is None:
            raise ValueError("Action is unavailable")
        decision = {"proposal_key": proposal_key, "product_id": insight["product_id"],
                    "store_id": store_id, "action": action, "status": "approved",
                    "baseline": insight["counts"], "quantity": choice["quantity"],
                    "evidence_sessions": [e["session_id"] for e in insight["evidence"]]}
        if action == "transfer":
            db.transfer_stock(insight["product_id"], choice["source_store_id"], store_id, choice["quantity"])
            decision.update(source_store_id=choice["source_store_id"], execution="local_inventory_simulation")
        elif action == "replenish":
            po = db.insert_purchase_order({"product_id": insight["product_id"], "store_id": store_id,
                "product_name": insight["product_name"], "quantity": choice["quantity"], "urgency": "high",
                "justification": insight["summary"], "human_approval_required": True})
            decision.update(po_id=po["po_id"], execution="purchase_order_drafted")
        else:
            decision["execution"] = "observation_only"
        return db.save_decision(proposal_key, decision)


def decide_discount(product_id: str, store_id: str, status: str) -> dict:
    from tools.pulse_tools.execute_perishable_discount import (
        execute_perishable_discount,
    )

    if status not in {"approved", "rejected"}:
        raise ValueError("Invalid discount decision")
    db = get_alloydb()
    with db.transaction():
        proposal = next((p for p in execute_perishable_discount(store_id)["perishable_alerts"]
                         if p["product_id"] == product_id), None)
        if proposal is None:
            raise ValueError("Discount proposal expired or not found")
        key = f"discount:{store_id}:{product_id}:{proposal['expiry_date']}"
        decision = db.save_decision(key, {"product_id": product_id, "store_id": store_id,
            "status": status, "action": "discount", "discount_pct": proposal["discount_pct"]})
        if status == "approved":
            db.set_discount_active(product_id, True, store_id, proposal["discount_pct"])
        return decision
