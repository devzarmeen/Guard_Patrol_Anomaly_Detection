from datetime import datetime
from unittest.mock import patch
from urllib.error import URLError

from sqlmodel import select

from app.models import AlertLog
from app.services.alerting import send_alerts_for_events


def _critical_event():
    return {
        "guard_id": "G001",
        "event_id": 1,
        "event_risk_level": "Critical",
        "max_hybrid_score": 0.8,
        "event_classification": "Strong Anomaly",
        "description": "Extreme speed",
        "latitude": 51.5,
        "longitude": -0.12,
        "start_time": datetime(2026, 8, 13, 8, 40),
        "end_time": datetime(2026, 8, 13, 8, 41),
    }


def test_alerting_skips_when_channels_are_not_configured(session):
    results = send_alerts_for_events(session, [_critical_event()])
    channels = {item["channel"] for item in results}
    assert "email" in channels
    assert "webhook" in channels
    assert all(item["status"] == "skipped" for item in results)


def test_alerting_does_not_repeat_skipped_logs(session):
    send_alerts_for_events(session, [_critical_event()])
    send_alerts_for_events(session, [_critical_event()])
    logs = session.exec(select(AlertLog)).all()
    assert len(logs) == 2
    assert {log.channel for log in logs} == {"email", "webhook"}


def test_webhook_serializes_datetime_payload(session, monkeypatch):
    monkeypatch.setenv("WEBHOOK_URL", "https://example.test/alerts")
    captured: dict[str, bytes] = {}

    class FakeResponse:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout=15):
        captured["body"] = req.data
        captured["timeout"] = timeout
        return FakeResponse()

    with patch("app.services.alerting.request.urlopen", side_effect=fake_urlopen):
        results = send_alerts_for_events(session, [_critical_event()])

    webhook = next(item for item in results if item["channel"] == "webhook")
    assert webhook["status"] == "sent"
    assert b"2026-08-13T08:40:00" in captured["body"]


def test_email_failure_does_not_raise(session, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("ALERT_EMAIL_TO", "ops@example.test")

    with patch(
        "app.services.alerting.smtplib.SMTP",
        side_effect=OSError("connection refused"),
    ):
        results = send_alerts_for_events(session, [_critical_event()])

    email = next(item for item in results if item["channel"] == "email")
    assert email["status"] == "failed"
    assert "connection refused" in (email["error"] or "")


def test_failed_webhook_is_retried(session, monkeypatch):
    monkeypatch.setenv("WEBHOOK_URL", "https://example.test/alerts")

    with patch(
        "app.services.alerting.request.urlopen",
        side_effect=URLError("timeout"),
    ):
        first = send_alerts_for_events(session, [_critical_event()])
    assert next(item for item in first if item["channel"] == "webhook")["status"] == "failed"

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch("app.services.alerting.request.urlopen", return_value=FakeResponse()):
        second = send_alerts_for_events(session, [_critical_event()])
    assert next(item for item in second if item["channel"] == "webhook")["status"] == "sent"
