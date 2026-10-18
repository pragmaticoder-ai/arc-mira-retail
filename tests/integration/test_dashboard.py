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
    at = AppTest.from_file(str(ROOT / "frontend/pulse-dashboard/pulse_dashboard.py"), default_timeout=20).run()
    assert not at.exception
    next(b for b in at.button if b.label == "Approve selected action").click().run()
    assert not at.exception
    assert any("Manager decision: transfer" in s.value for s in at.success)
    next(b for b in at.button if b.label == "Approve discount").click().run()
    assert not at.exception
    assert any("Discount approved" in s.value for s in at.success)
    next(b for b in at.button if b.label == "Approve PO").click().run()
    assert not at.exception
    next(b for b in at.button if b.label == "Refresh now").click().run()
    assert not at.exception
    assert not any(b.label == "Approve PO" for b in at.button)
