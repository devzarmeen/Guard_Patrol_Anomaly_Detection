from datetime import datetime

from app.services.alerting import send_alerts_for_events


def test_alerting_skips_when_channels_are_not_configured(session):
    events = [
        {
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
    ]
    results = send_alerts_for_events(session, events)
    channels = {item["channel"] for item in results}
    assert "email" in channels
    assert "webhook" in channels
    assert all(item["status"] == "skipped" for item in results)
