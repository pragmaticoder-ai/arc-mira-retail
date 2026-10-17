"""BigQuery adapter (the ARIA->PULSE bridge) — placeholder with mock impl.

Bridge tables: incidents (ARIA writes, PULSE reads), inventory_log,
promotion_log. Also the demand_forecast ARIMA_PLUS model used by
predict_stockout(). Tools call these methods, never the BigQuery SDK directly.

Mock keeps the incidents table in process memory so ARIA's log_session write
is immediately visible to PULSE's detect_patterns read — the bridge works
end-to-end offline. ARIMA_PLUS has no emulator, so forecast_stockout() returns
a canned prediction in mock mode (real impl TODO calls BigQuery ML).
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from abc import ABC, abstractmethod
from collections import Counter
from datetime import datetime, timedelta

from tools.shared.settings import settings


class BigQueryClient(ABC):
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
        record = {**incident, "session_id": sid}
        self._incidents[sid] = record  # idempotent on session_id
        return {"session_id": sid, "logged": True, "timestamp": datetime.now().isoformat()}

    def detect_stockout_patterns(self, *, store_id: str, hours: int, min_incidents: int) -> list[dict]:
        return _aggregate_patterns(
            list(self._incidents.values()), store_id=store_id, hours=hours, min_incidents=min_incidents
        )

    def forecast_stockout(self, *, product_id: str, store_id: str, forecast_days: int) -> dict:
        # ARIMA_PLUS cannot be emulated locally — return a canned forecast.
        return {
            "predicted_stockout_date": "2026-10-20",
            "days_until_stockout": 3,
            "confidence": 0.82,
            "current_stock": 0,
            "daily_consumption_rate": 4.5,
            "evidence": {
                "model": "BigQuery ML ARIMA_PLUS (mock)",
                "training_period": "Oct 1–17 2026",
                "data_points_used": 17,
            },
        }

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
    cutoff = datetime(2026, 10, 17, 11, 0, 0) - timedelta(hours=hours)
    agg: dict[str, dict] = {}
    for inc in incidents:
        if inc.get("store_id") != store_id:
            continue
        try:
            ts = datetime.fromisoformat(inc["timestamp"])
        except (KeyError, ValueError):
            continue
        if ts < cutoff:
            continue
        for item in inc.get("items_unavailable", []):
            pid = item.get("product_id")
            if not pid:
                continue
            a = agg.setdefault(pid, {
                "name": item.get("product_name", pid), "count": 0, "carts": [],
                "abandon": 0, "first": ts, "last": ts, "sessions": [],
                "subs_total": 0, "subs_accepted": 0, "hours": Counter(),
            })
            a["count"] += 1
            a["carts"].append(float(inc.get("cart_total_aed", 0.0)))
            if not inc.get("order_placed", True):
                a["abandon"] += 1
            a["first"] = min(a["first"], ts)
            a["last"] = max(a["last"], ts)
            if len(a["sessions"]) < 3:
                a["sessions"].append(inc.get("session_id", ""))
            a["hours"][ts.hour] += 1
            for s in inc.get("substitutions_offered", []):
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


_CANNED_FORECAST = {
    "predicted_stockout_date": "2026-10-20", "days_until_stockout": 3, "confidence": 0.82,
    "current_stock": 0, "daily_consumption_rate": 4.5,
    "evidence": {"model": "BigQuery ML ARIMA_PLUS (mock)", "training_period": "Oct 1–17 2026", "data_points_used": 17},
}
_VELOCITIES = {"laban_almarai_1l": 8.5, "milk_almarai_2l": 12.0, "bread_white_loaf": 15.0, "croissant_4pk": 5.0}


def _demo_seed_incidents() -> list[dict]:
    """The Mon–Wed 10:00-12:00 brown-rice stockout cluster (shared seed)."""
    slots = [
        datetime(2026, 10, 15, 10, 15), datetime(2026, 10, 15, 11, 30),
        datetime(2026, 10, 16, 10, 5), datetime(2026, 10, 16, 11, 45),
        datetime(2026, 10, 16, 10, 50), datetime(2026, 10, 17, 10, 20),
        datetime(2026, 10, 17, 11, 10), datetime(2026, 10, 17, 10, 40),
    ]
    rows = []
    for i in range(8):
        rows.append({
            "session_id": f"seed_sess_{i:02d}", "customer_id": "sarah_123",
            "store_id": "dubai_marina_01", "timestamp": slots[i].isoformat(),
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
        # INSERT OR IGNORE = idempotent on session_id (primary key).
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO arc_incidents(session_id, payload) VALUES (?, ?)",
                (sid, json.dumps(record)),
            )
        return {"session_id": sid, "logged": True, "timestamp": datetime.now().isoformat()}

    def detect_stockout_patterns(self, *, store_id: str, hours: int, min_incidents: int) -> list[dict]:
        return _aggregate_patterns(self._all_incidents(), store_id=store_id, hours=hours, min_incidents=min_incidents)

    def forecast_stockout(self, *, product_id: str, store_id: str, forecast_days: int) -> dict:
        return dict(_CANNED_FORECAST)

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
    """TODO(backend): implement with google.cloud.bigquery. Note ARIMA_PLUS has
    no local emulator, so forecast_stockout must run against real BigQuery ML."""

    def __init__(self) -> None:
        raise NotImplementedError(
            "RealBigQueryClient not implemented. Set USE_MOCK=true or wire BigQuery "
            f"(dataset={settings.bigquery_dataset})."
        )

    def insert_incident(self, incident: dict) -> dict: ...
    def detect_stockout_patterns(self, *, store_id: str, hours: int, min_incidents: int) -> list[dict]: ...
    def forecast_stockout(self, *, product_id: str, store_id: str, forecast_days: int) -> dict: ...
    def get_daily_sales_rate(self, *, product_id: str, store_id: str, days: int = 7) -> float: ...
    def record_substitution_gap(self, *, product_id: str, store_id: str) -> str: ...


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
