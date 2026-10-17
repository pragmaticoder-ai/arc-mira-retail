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


class MockBigQueryClient(BigQueryClient):
    def __init__(self) -> None:
        self._incidents: dict[str, dict] = {}
        self._seed_demo_incidents()

    def _seed_demo_incidents(self) -> None:
        """Pre-load the brown-rice stockout pattern so PULSE has data on a
        cold start, even before ARIA logs a live session during the demo."""
        now = datetime(2026, 10, 17, 11, 0, 0)
        for i in range(8):
            sid = f"seed_sess_{i:02d}"
            self._incidents[sid] = {
                "session_id": sid,
                "customer_id": "sarah_123",
                "store_id": "dubai_marina_01",
                "timestamp": (now - timedelta(hours=46 - i * 5)).isoformat(),
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
        counter: Counter[str] = Counter()
        names: dict[str, str] = {}
        carts: dict[str, list[float]] = {}
        abandonments: Counter[str] = Counter()
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
                counter[pid] += 1
                names[pid] = item.get("product_name", pid)
                carts.setdefault(pid, []).append(float(inc.get("cart_total_aed", 0.0)))
                if not inc.get("order_placed", True):
                    abandonments[pid] += 1

        patterns = []
        for pid, count in counter.most_common():
            if count < min_incidents:
                continue
            avg_cart = sum(carts[pid]) / len(carts[pid]) if carts[pid] else 0.0
            patterns.append(
                {
                    "product_id": pid,
                    "product_name": names[pid],
                    "store_id": store_id,
                    "incident_count": count,
                    "period_hours": hours,
                    "estimated_revenue_lost_aed": round(count * avg_cart * 0.15, 2),
                    "abandonment_count": abandonments[pid],
                    "average_cart_aed": round(avg_cart, 2),
                }
            )
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


_client: BigQueryClient | None = None


def get_bigquery() -> BigQueryClient:
    global _client
    if _client is None:
        _client = MockBigQueryClient() if settings.use_mock else RealBigQueryClient()
    return _client
