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
        """Pre-load the brown-rice stockout pattern so PULSE has data on a
        cold start. Incidents cluster in the Mon–Wed 10:00–12:00 morning peak
        (the documented scenario), so the computed peak window is 10:00-12:00
        and the gap vs the Tuesday 14:00 delivery is ~4h."""
        # Oct 13 = Mon, 14 = Tue, 15 = Wed, 2026. Spread 8 incidents across
        # those mornings at 10:00/11:00.
        slots = [
            datetime(2026, 10, 15, 10, 15), datetime(2026, 10, 15, 11, 30),
            datetime(2026, 10, 16, 10, 5), datetime(2026, 10, 16, 11, 45),
            datetime(2026, 10, 16, 10, 50), datetime(2026, 10, 17, 10, 20),
            datetime(2026, 10, 17, 11, 10), datetime(2026, 10, 17, 10, 40),
        ]
        for i in range(8):
            sid = f"seed_sess_{i:02d}"
            self._incidents[sid] = {
                "session_id": sid,
                "customer_id": "sarah_123",
                "store_id": "dubai_marina_01",
                "timestamp": slots[i].isoformat(),
                "items_ordered": [],
                "items_unavailable": [{"product_id": "rice_brown_500g", "product_name": "Brown Rice 500g"}],
                "substitutions_offered": [{"original_product_id": "rice_brown_500g", "substitute_product_id": "rice_basmati_5kg", "accepted": i % 2 == 0}],
                "cart_total_aed": 285.0,
                "session_sentiment": "neutral",
                "order_placed": i % 3 != 0,
                "abandonment_reason": None if i % 3 != 0 else "item_unavailable",
            }

    def insert_incident(self, incident: dict) -> dict:
        sid = incident.get("session_id") or str(uuid.uuid4())
        record = {**incident, "session_id": sid}
        self._incidents[sid] = record  # idempotent on session_id
        return {"session_id": sid, "logged": True, "timestamp": datetime.now().isoformat()}

    def detect_stockout_patterns(self, *, store_id: str, hours: int, min_incidents: int) -> list[dict]:
        cutoff = datetime(2026, 10, 17, 11, 0, 0) - timedelta(hours=hours)
        # Per-product accumulators.
        agg: dict[str, dict] = {}
        for inc in self._incidents.values():
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
            peak_hour_num = a["hours"].most_common(1)[0][0] if a["hours"] else 10
            sub_rate = round(a["subs_accepted"] / a["subs_total"], 2) if a["subs_total"] else 0.0
            patterns.append(
                {
                    "product_id": pid,
                    "product_name": a["name"],
                    "store_id": store_id,
                    "incident_count": a["count"],
                    "period_hours": hours,
                    "estimated_revenue_lost_aed": round(a["count"] * avg_cart * 0.15, 2),
                    "abandonment_count": a["abandon"],
                    "average_cart_aed": round(avg_cart, 2),
                    "peak_hour": f"{peak_hour_num:02d}:00-{peak_hour_num + 2:02d}:00",
                    "evidence": {
                        "first_incident": a["first"].isoformat(),
                        "last_incident": a["last"].isoformat(),
                        "sample_session_ids": a["sessions"],
                        "substitution_acceptance_rate": sub_rate,
                    },
                }
            )
        patterns.sort(key=lambda p: p["estimated_revenue_lost_aed"], reverse=True)
        return patterns

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
    global _client
    if _client is None:
        _client = MockBigQueryClient() if settings.use_mock else RealBigQueryClient()
    return _client
