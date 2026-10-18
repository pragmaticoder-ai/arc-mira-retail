"""Manager UI writes persist before success is rendered."""

from pathlib import Path

import pytest

st = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def test_manager_action_and_discount_buttons(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "frontend/pulse-dashboard"))
    # Exercise the actual UI without scheduling repeated fragment reruns.
    monkeypatch.setattr(st, "fragment", lambda *args, **kwargs: lambda fn: fn)
    at = AppTest.from_file(
        str(ROOT / "frontend/pulse-dashboard/pulse_dashboard.py"), default_timeout=20
    ).run()
    assert not at.exception
    at.radio[0].set_value("Unmet demand").run()
    next(b for b in at.button if b.label == "Approve selected action").click().run()
    assert not at.exception
    assert any("Manager decision: transfer" in s.value for s in at.success)
    at.radio[0].set_value("Perishables").run()
    next(b for b in at.button if b.label == "Approve discount").click().run()
    assert not at.exception
    assert any("Discount approved" in s.value for s in at.success)
    at.radio[0].set_value("Stockout alerts").run()
    next(b for b in at.button if b.label == "View alert details").click().run()
    next(b for b in at.button if b.label == "Approve & restock (demo)").click().run()
    assert not at.exception
    next(b for b in at.button if b.label == "Refresh now").click().run()
    assert not at.exception
    assert not any(b.label == "Approve & restock (demo)" for b in at.button)


def test_all_dashboard_pages_history_rejection_and_customer_activity(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "frontend/pulse-dashboard"))
    monkeypatch.setattr(st, "fragment", lambda *args, **kwargs: lambda fn: fn)
    from tools.shared.alloydb_client import get_alloydb
    db = get_alloydb()
    db.save_session("demo-session", {"session_id": "demo-session", "store_id": "dubai_marina_01", "customer_id": "sarah_123", "cart": {"items": [], "total_aed": 0}})
    at = AppTest.from_file(str(ROOT / "frontend/pulse-dashboard/pulse_dashboard.py"), default_timeout=20).run()
    assert not at.exception
    at.radio[0].set_value("Perishables").run()
    next(b for b in at.button if b.label == "Reject discount").click().run()
    assert not at.exception
    assert any("rejected" in v.value for v in at.success)
    at.radio[0].set_value("Action history").run()
    assert not at.exception
    assert any("Rejected" in df.value.to_string() for df in at.dataframe)
    at.radio[0].set_value("Customer activity").run()
    assert not at.exception
    assert any("Sarah" in df.value.to_string() for df in at.dataframe)
    for page in ["Stockout alerts", "Unmet demand", "Overview"]:
        at.radio[0].set_value(page).run()
        assert not at.exception
    # Store / period changes and refresh must not leave broken drill-in state.
    at.selectbox(key="active_store").set_value("jbr_01").run()
    at.selectbox[1].set_value(168).run()
    next(b for b in at.button if b.label == "Refresh now").click().run()
    assert not at.exception
