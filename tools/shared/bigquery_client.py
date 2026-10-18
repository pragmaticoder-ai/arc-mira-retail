"""Incident bridge with memory and durable SQLite implementations.

Bridge tables: incidents (ARIA writes, PULSE reads), inventory_log,
promotion_log. Also the demand_forecast ARIMA_PLUS model used by
predict_stockout(). Tools call these methods, never the BigQuery SDK directly.

Mock keeps the incidents table in process memory so ARIA's log_session write
is immediately visible to PULSE's detect_patterns read — the bridge works
end-to-end offline. ARIMA_PLUS has no emulator, so forecast_stockout() returns
a canned prediction in mock mode (real impl TODO calls BigQuery ML).
"""

from __future__ import annotations

import copy
import json
import math
import sqlite3
import threading
import uuid
from abc import ABC, abstractmethod
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from tools.shared.clock import now, today
from tools.shared.settings import settings


class BigQueryClient(ABC):
    def list_incidents(self, store_id: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def insert_incident(self, incident: dict) -> dict:
        """ARIA log_session write to arc_dataset.incidents (idempotent on session_id)."""

    @abstractmethod
    def detect_stockout_patterns(self, *, store_id: str, hours: int, min_incidents: int) -> list[dict]:
        """PULSE read: products with >= min_incidents stockouts in the window."""

    @abstractmethod
    def forecast_stockout(self, *, product_id: str, store_id: str, forecast_days: int) -> dict:
        """BigQuery ML ARIMA_PLUS forecast (canned in mock mode)."""

    @abstractmethod
    def get_daily_sales_rate(self, *, product_id: str, store_id: str, days: int = 7) -> float:
        """7-day sell-through velocity (units/day) from incidents."""

    @abstractmethod
    def record_substitution_gap(self, *, product_id: str, store_id: str) -> str:
        """Record that no substitute was found for a product at a store.
        Returns "new" the first time, "recurring" thereafter — a signal the
        store manager / PULSE can act on."""


class MockBigQueryClient(BigQueryClient):
    def __init__(self) -> None:
        self._incidents: dict[str, dict] = {}
        self._substitution_gaps: dict[tuple[str, str], int] = {}
        self._seed_demo_incidents()

    def _seed_demo_incidents(self) -> None:
        """Pre-load the brown-rice stockout pattern (shared seed) so PULSE has
        data on a cold start. Clusters in the Mon–Wed 10:00-12:00 peak."""
        for row in _demo_seed_incidents():
            self._incidents[row["session_id"]] = row

    def insert_incident(self, incident: dict) -> dict:
        sid = incident.get("session_id") or str(uuid.uuid4())
        previous = self._incidents.get(sid, {})
        record = {**incident, "session_id": sid, "timestamp": previous.get("timestamp", incident.get("timestamp", now().isoformat()))}
        self._incidents[sid] = record  # idempotent on session_id
        return {"session_id": sid, "logged": True, "timestamp": now().isoformat()}

    def detect_stockout_patterns(self, *, store_id: str, hours: int, min_incidents: int) -> list[dict]:
        return _aggregate_patterns(
            list(self._incidents.values()), store_id=store_id, hours=hours, min_incidents=min_incidents
        )

    def list_incidents(self, store_id: str) -> list[dict]:
        return [r for r in self._incidents.values() if r.get("store_id") == store_id]

    def forecast_stockout(self, *, product_id: str, store_id: str, forecast_days: int) -> dict:
        return _local_forecast(product_id, store_id, forecast_days)

    def get_daily_sales_rate(self, *, product_id: str, store_id: str, days: int = 7) -> float:
        # Mock velocities keyed to the demo. Laban sells ~8.5/day (drives the
        # perishable trigger). Unknown products default to a modest rate.
        rates = {
            "laban_almarai_1l": 8.5,
            "milk_almarai_2l": 12.0,
            "bread_white_loaf": 15.0,
            "croissant_4pk": 5.0,
        }
        return rates.get(product_id, 3.0)

    def record_substitution_gap(self, *, product_id: str, store_id: str) -> str:
        key = (product_id, store_id)
        count = self._substitution_gaps.get(key, 0)
        self._substitution_gaps[key] = count + 1
        return "new" if count == 0 else "recurring"


# ── Shared aggregation used by both mock + sqlite (identical semantics) ──
def _aggregate_patterns(incidents: list[dict], *, store_id: str, hours: int, min_incidents: int) -> list[dict]:
    cutoff = now() - timedelta(hours=hours)
    agg: dict[str, dict] = {}
    for inc in incidents:
        if inc.get("store_id") != store_id:
            continue
        try:
            ts = datetime.fromisoformat(inc["timestamp"])
        except (KeyError, ValueError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=now().tzinfo)
        if ts < cutoff or ts > now():
            continue
        seen = set()
        for item in inc.get("items_unavailable", []):
            pid = item.get("product_id")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            a = agg.setdefault(pid, {
                "name": item.get("product_name", pid), "count": 0, "carts": [],
                "abandon": 0, "first": ts, "last": ts, "sessions": [],
                "subs_total": 0, "subs_accepted": 0, "hours": Counter(),
            })
            a["count"] += 1
            a["carts"].append(float(inc.get("cart_total_aed", 0.0)))
            if inc.get("session_status") == "abandoned" or ("session_status" not in inc and not inc.get("order_placed", True)):
                a["abandon"] += 1
            a["first"] = min(a["first"], ts)
            a["last"] = max(a["last"], ts)
            if len(a["sessions"]) < 3:
                a["sessions"].append(inc.get("session_id", ""))
            a["hours"][ts.hour] += 1
            for s in inc.get("substitutions_offered", []):
                if s.get("original_product_id") != pid:
                    continue
                a["subs_total"] += 1
                if s.get("accepted"):
                    a["subs_accepted"] += 1

    patterns = []
    for pid, a in agg.items():
        if a["count"] < min_incidents:
            continue
        avg_cart = sum(a["carts"]) / len(a["carts"]) if a["carts"] else 0.0
        peak = a["hours"].most_common(1)[0][0] if a["hours"] else 10
        sub_rate = round(a["subs_accepted"] / a["subs_total"], 2) if a["subs_total"] else 0.0
        patterns.append({
            "product_id": pid, "product_name": a["name"], "store_id": store_id,
            "incident_count": a["count"], "period_hours": hours,
            "estimated_revenue_lost_aed": round(a["count"] * avg_cart * 0.15, 2),
            "abandonment_count": a["abandon"], "average_cart_aed": round(avg_cart, 2),
            "peak_hour": f"{peak:02d}:00-{peak + 2:02d}:00",
            "evidence": {
                "first_incident": a["first"].isoformat(),
                "last_incident": a["last"].isoformat(),
                "sample_session_ids": a["sessions"],
                "substitution_acceptance_rate": sub_rate,
            },
        })
    patterns.sort(key=lambda p: p["estimated_revenue_lost_aed"], reverse=True)
    return patterns


def _local_forecast(product_id: str, store_id: str, forecast_days: int) -> dict:
    from tools.shared.alloydb_client import get_alloydb

    product = get_alloydb().get_product_at_store(product_id, store_id) or {}
    stock = product.get("stock_quantity", 0)
    rate = _VELOCITIES.get(product_id, 3.0)
    days = math.ceil(stock / rate)
    return {"predicted_stockout_date": (today() + timedelta(days=days)).isoformat(),
            "days_until_stockout": days, "confidence": 0.82,
            "current_stock": stock, "daily_consumption_rate": rate,
            "evidence": {"model": "Synthetic depletion scenario; not BigQuery ML",
                         "training_period": "One seeded daily-velocity assumption",
                         "data_points_used": 1, "forecast_horizon_days": forecast_days,
                         "confidence_note": "Illustrative fixture value, not calibrated statistical confidence"}}


_VELOCITIES = {"laban_almarai_1l": 8.5, "milk_almarai_2l": 12.0, "bread_white_loaf": 15.0, "croissant_4pk": 5.0}


def _demo_seed_incidents() -> list[dict]:
    """The Mon–Wed 10:00-12:00 brown-rice stockout cluster (shared seed)."""
    slots = [now() - timedelta(hours=h) for h in (40, 38, 28, 26, 25, 12, 10, 8)]
    rows = []
    for i in range(8):
        rows.append({
            "session_id": f"seed_sess_{i:02d}", "customer_id": "sarah_123",
            "store_id": "dubai_marina_01", "timestamp": slots[i].isoformat(),
            "data_origin": "synthetic_seed",
            "demand_signals": [{"product_id": "rice_brown_500g", "product_name": "Brown Rice 500g",
                "outcome": ("compromise" if i < 4 else "rejected" if i < 6 else "satisfied"),
                "evidence": ("The alternative is okay this time; please restock brown rice." if i < 4 else "No thanks, I only want brown rice." if i < 6 else "I am happy with the alternative."),
                "certainty": "explicit", "evidence_source": "synthetic_customer_statement"}],
            "items_ordered": [], "items_unavailable": [{"product_id": "rice_brown_500g", "product_name": "Brown Rice 500g"}],
            "substitutions_offered": [{"original_product_id": "rice_brown_500g", "substitute_product_id": "rice_basmati_5kg", "accepted": i % 2 == 0}],
            "cart_total_aed": 285.0, "session_sentiment": "neutral",
            "order_placed": i % 3 != 0, "abandonment_reason": None if i % 3 != 0 else "item_unavailable",
        })
    return rows


class SqliteBigQueryClient(BigQueryClient):
    """File-backed SQLite bridge (stdlib sqlite3) so ARIA + PULSE in SEPARATE
    processes share the incidents table. Same interface + semantics as the mock;
    only storage differs. Selected when settings.arc_bridge_db is set."""

    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        # Lock first — the seed loop below calls insert_incident, which locks.
        self._lock = threading.Lock()
        # check_same_thread=False: Streamlit reruns the script on different
        # threads and reuses this singleton. Our calls are short, autocommit,
        # and serialized by self._lock, so cross-thread use is safe here.
        self._conn = sqlite3.connect(
            db_path, isolation_level=None, check_same_thread=False
        )  # autocommit
        self._conn.execute("PRAGMA journal_mode=WAL")  # safe concurrent readers
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS arc_incidents (session_id TEXT PRIMARY KEY, payload TEXT)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS arc_sub_gaps (product_id TEXT, store_id TEXT, n INTEGER, PRIMARY KEY(product_id, store_id))"
        )
        # Seed demo incidents once (idempotent on session_id).
        cur = self._conn.execute("SELECT COUNT(*) FROM arc_incidents")
        if cur.fetchone()[0] == 0:
            for row in _demo_seed_incidents():
                self.insert_incident(row)

    def _all_incidents(self) -> list[dict]:
        with self._lock:
            cur = self._conn.execute("SELECT payload FROM arc_incidents")
            rows = cur.fetchall()
        return [json.loads(r[0]) for r in rows]

    def insert_incident(self, incident: dict) -> dict:
        sid = incident.get("session_id") or str(uuid.uuid4())
        record = {**incident, "session_id": sid}
        # Update a session as feedback and checkout arrive; one row per session.
        with self._lock:
            old = self._conn.execute("SELECT payload FROM arc_incidents WHERE session_id=?", (sid,)).fetchone()
            if old:
                record["timestamp"] = json.loads(old[0])["timestamp"]
            self._conn.execute(
                "INSERT INTO arc_incidents(session_id, payload) VALUES (?, ?) ON CONFLICT(session_id) DO UPDATE SET payload=excluded.payload",
                (sid, json.dumps(record)),
            )
        return {"session_id": sid, "logged": True, "timestamp": now().isoformat()}

    def list_incidents(self, store_id: str) -> list[dict]:
        return [r for r in self._all_incidents() if r.get("store_id") == store_id]

    def detect_stockout_patterns(self, *, store_id: str, hours: int, min_incidents: int) -> list[dict]:
        return _aggregate_patterns(self._all_incidents(), store_id=store_id, hours=hours, min_incidents=min_incidents)

    def forecast_stockout(self, *, product_id: str, store_id: str, forecast_days: int) -> dict:
        return _local_forecast(product_id, store_id, forecast_days)

    def get_daily_sales_rate(self, *, product_id: str, store_id: str, days: int = 7) -> float:
        return _VELOCITIES.get(product_id, 3.0)

    def record_substitution_gap(self, *, product_id: str, store_id: str) -> str:
        with self._lock:
            cur = self._conn.execute(
                "SELECT n FROM arc_sub_gaps WHERE product_id=? AND store_id=?", (product_id, store_id)
            )
            row = cur.fetchone()
            n = row[0] if row else 0
            self._conn.execute(
                "INSERT INTO arc_sub_gaps(product_id, store_id, n) VALUES (?,?,?) "
                "ON CONFLICT(product_id, store_id) DO UPDATE SET n=?",
                (product_id, store_id, n + 1, n + 1),
            )
        return "new" if n == 0 else "recurring"


class RealBigQueryClient(BigQueryClient):
    """Production Google Cloud BigQuery adapter for incidents bridge and BigQuery ML."""

    def __init__(self) -> None:
        from google.cloud import bigquery

        self.client = bigquery.Client(
            project=settings.google_cloud_project,
            location=settings.bigquery_location,
        )
        self._incident_cache: dict[str, tuple[datetime, list[dict]]] = {}
        self.dataset_id = settings.bigquery_dataset
        self.table_ref = f"{settings.google_cloud_project}.{self.dataset_id}.incidents"

    def insert_incident(self, incident: dict) -> dict:
        sid = incident.get("session_id") or str(uuid.uuid4())
        ts = incident.get("timestamp") or now().isoformat()
        row = {
            "session_id": sid,
            "customer_id": incident.get("customer_id"),
            "store_id": incident.get("store_id"),
            "timestamp": ts,
            "items_ordered": json.dumps(incident.get("items_ordered", [])),
            "items_unavailable": json.dumps(incident.get("items_unavailable", [])),
            "demand_signals": json.dumps(incident.get("demand_signals", [])),
            "requested_items": json.dumps(incident.get("requested_items", [])),
            "session_status": incident.get("session_status", "completed"),
            "substitutions_offered": json.dumps(incident.get("substitutions_offered", [])),
            "promotion_id": incident.get("promotion_id"),
            "promotion_saving_aed": float(incident.get("promotion_saving_aed") or 0.0),
            "cart_total_aed": float(incident.get("cart_total_aed") or 0.0),
            "budget_aed": float(incident.get("budget_aed") or 0.0),
            "session_sentiment": incident.get("session_sentiment", "neutral"),
            "order_placed": bool(incident.get("order_placed", False)),
            "abandonment_reason": incident.get("abandonment_reason"),
        }
        from google.cloud import bigquery

        # DML upsert preserves one current row per session and is immediately
        # queryable. Streaming insert IDs do not deduplicate changed feedback.
        strings = {"customer_id", "store_id", "session_status", "promotion_id",
                   "session_sentiment", "abandonment_reason"}
        arrays = {"items_ordered", "items_unavailable", "demand_signals", "requested_items", "substitutions_offered"}
        expressions = {}
        for key, value in row.items():
            if key == "session_id":
                expressions[key] = "S.session_id"
            elif key in arrays:
                # row's JSON columns are serialized strings for the SDK.
                row[key] = json.loads(value)
                expressions[key] = f"JSON_QUERY(S.payload, '$.{key}')"
            elif key in strings:
                expressions[key] = f"JSON_VALUE(S.payload, '$.{key}')"
            else:
                kind = "TIMESTAMP" if key == "timestamp" else "BOOL" if key == "order_placed" else "FLOAT64"
                expressions[key] = f"SAFE_CAST(JSON_VALUE(S.payload, '$.{key}') AS {kind})"
        columns = list(expressions)
        update = ", ".join(f"{k}={expressions[k]}" for k in columns if k not in {"session_id", "timestamp"})
        query = f"""MERGE `{self.table_ref}` T
            USING (SELECT @sid session_id, PARSE_JSON(@payload) payload) S
            ON T.session_id=S.session_id
            WHEN MATCHED THEN UPDATE SET {update}
            WHEN NOT MATCHED THEN INSERT ({', '.join(columns)})
            VALUES ({', '.join(expressions.values())})"""
        config = bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("sid", "STRING", sid),
            bigquery.ScalarQueryParameter("payload", "STRING", json.dumps(row))])
        self.client.query(query, job_config=config).result()
        self._incident_cache.pop(incident.get("store_id", ""), None)
        return {"session_id": sid, "logged": True, "timestamp": ts}

    def list_incidents(self, store_id: str) -> list[dict]:
        from google.cloud import bigquery

        cached = self._incident_cache.get(store_id)
        if cached and (now() - cached[0]).total_seconds() < 5:
            return copy.deepcopy(cached[1])
        query = f"""
            SELECT session_id, customer_id, store_id, timestamp,
                   items_ordered, items_unavailable, demand_signals, requested_items,
                   session_status, substitutions_offered, promotion_id, promotion_saving_aed,
                   cart_total_aed, budget_aed, session_sentiment, order_placed, abandonment_reason
            FROM `{self.table_ref}`
            WHERE store_id = @store_id
              AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            ORDER BY timestamp DESC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("store_id", "STRING", store_id)]
        )
        results = self.client.query(query, job_config=job_config)
        incidents = []
        for r in results:
            d = dict(r.items())
            for k in ("items_ordered", "items_unavailable", "demand_signals", "requested_items", "substitutions_offered"):
                val = d.get(k)
                if isinstance(val, str):
                    try:
                        d[k] = json.loads(val)
                    except Exception:
                        d[k] = []
            if d.get("timestamp"):
                d["timestamp"] = d["timestamp"].isoformat()
            incidents.append(d)
        self._incident_cache[store_id] = (now(), copy.deepcopy(incidents))
        return incidents

    def detect_stockout_patterns(self, *, store_id: str, hours: int, min_incidents: int) -> list[dict]:
        incidents = self.list_incidents(store_id)
        return _aggregate_patterns(incidents, store_id=store_id, hours=hours, min_incidents=min_incidents)

    def forecast_stockout(self, *, product_id: str, store_id: str, forecast_days: int) -> dict:
        from tools.shared.alloydb_client import get_alloydb

        product = get_alloydb().get_product_at_store(product_id, store_id)
        stock = product["stock_quantity"] if product else 0
        rate = self.get_daily_sales_rate(product_id=product_id, store_id=store_id)
        return {"confidence": 0.0, "predicted_stockout_date": None,
                "days_until_stockout": None, "current_stock": stock,
                "daily_consumption_rate": rate,
                "evidence": "Observed confirmed-order units over 7 days; no trained stockout model. Date suppressed."}

    def get_daily_sales_rate(self, *, product_id: str, store_id: str, days: int = 7) -> float:
        cutoff = now() - timedelta(days=days)
        total = 0
        for row in self.list_incidents(store_id):
            stamp = datetime.fromisoformat(row["timestamp"])
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=now().tzinfo)
            if row.get("order_placed") and cutoff <= stamp <= now():
                total += sum(int(i.get("quantity", 0)) for i in row.get("items_ordered", [])
                             if i.get("product_id") == product_id)
        return total / days

    def record_substitution_gap(self, *, product_id: str, store_id: str) -> str:
        from tools.shared.alloydb_client import get_alloydb

        db = get_alloydb()
        key = f"substitution_gap:{store_id}:{product_id}"
        with db.transaction():
            if db.get_decision(key):
                return "recurring"
            db.save_decision(key, {"status": "observed", "product_id": product_id,
                                   "store_id": store_id, "kind": "substitution_gap"})
        return "new"


_client: BigQueryClient | None = None


def get_bigquery() -> BigQueryClient:
    """Factory. Selection order keeps real GCP a pure config switch:
      use_mock=False            -> RealBigQueryClient   (real BigQuery)
      mock + ARC_BRIDGE_DB set  -> SqliteBigQueryClient (cross-process demo)
      mock (default)            -> MockBigQueryClient   (in-memory, tests)
    No tool/agent/dashboard code changes when swapping to real BigQuery.
    """
    global _client
    if _client is None:
        if not settings.use_mock:
            _client = RealBigQueryClient()
        elif settings.arc_bridge_db:
            _client = SqliteBigQueryClient(settings.arc_bridge_db)
        else:
            _client = MockBigQueryClient()
    return _client
