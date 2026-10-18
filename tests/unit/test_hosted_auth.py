"""Hosted manager operations stay behind the demo sign-in gate."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGE = (
    Path(__file__).resolve().parents[2] / "frontend/pulse-dashboard/pulse_dashboard.py"
)


def test_hosted_manager_fails_closed_without_credentials(monkeypatch):
    monkeypatch.setenv("K_SERVICE", "test-pulse")
    monkeypatch.delenv("DEMO_USERNAME", raising=False)
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    app = AppTest.from_file(str(PAGE)).run()
    assert not app.exception
    assert "Manager access is not configured" in app.error[0].value
    assert not app.button


def test_manager_rejects_invalid_password_before_loading_operations(monkeypatch):
    monkeypatch.setenv("K_SERVICE", "test-pulse")
    monkeypatch.setenv("DEMO_USERNAME", "test-manager")
    monkeypatch.setenv("DEMO_PASSWORD", "test-only-password")
    app = AppTest.from_file(str(PAGE)).run()
    assert app.title[0].value == "PULSE manager sign in"
    app.text_input[0].set_value("test-manager")
    app.text_input[1].set_value("wrong-password")
    app.button[0].click().run()
    assert "Incorrect username or password" in app.error[0].value
    assert not app.selectbox
    assert not app.exception


def test_manager_accepts_credentials_and_can_sign_out(monkeypatch):
    monkeypatch.setenv("K_SERVICE", "test-pulse")
    monkeypatch.setenv("DEMO_USERNAME", "test-manager")
    monkeypatch.setenv("DEMO_PASSWORD", "test-only-password")
    app = AppTest.from_file(str(PAGE), default_timeout=20).run()
    app.text_input[0].set_value("test-manager")
    app.text_input[1].set_value("test-only-password")
    app.button[0].click().run()
    assert not app.exception
    assert any(button.label == "Sign out" for button in app.sidebar.button)
    next(
        button for button in app.sidebar.button if button.label == "Sign out"
    ).click().run()
    assert app.title[0].value == "PULSE manager sign in"
