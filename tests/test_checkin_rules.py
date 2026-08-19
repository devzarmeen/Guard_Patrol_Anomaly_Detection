from datetime import datetime, timedelta

from app.config import load_thresholds
from app.detection.checkins import classify_checkin


def test_late_and_normal_checkin_boundary():
    expected = datetime(2026, 8, 13, 8, 30)
    base = {
        "checkin_id": "CIX",
        "guard_id": "G001",
        "checkpoint_id": "CP001",
        "expected_time": expected,
        "latitude": 51.5074,
        "longitude": -0.1278,
        "gps_accuracy": 8,
    }

    normal = classify_checkin(
        {**base, "actual_time": expected + timedelta(minutes=10)}
    )
    late = classify_checkin(
        {**base, "actual_time": expected + timedelta(minutes=11)}
    )

    assert normal["status"] == "NORMAL"
    assert late["status"] == "LATE"
    assert late["anomaly_type"] == "CHECKIN_LATE"


def test_missed_checkin_uses_configured_wait():
    expected = datetime(2026, 8, 13, 8, 30)
    missed = classify_checkin(
        {
            "checkin_id": "CIY",
            "guard_id": "G002",
            "checkpoint_id": "CP002",
            "expected_time": expected,
            "actual_time": None,
        },
        now=expected + timedelta(minutes=31),
    )
    pending = classify_checkin(
        {
            "checkin_id": "CIZ",
            "guard_id": "G002",
            "checkpoint_id": "CP002",
            "expected_time": expected,
            "actual_time": None,
        },
        now=expected + timedelta(minutes=20),
    )
    assert missed["status"] == "MISSED"
    assert pending["status"] == "PENDING"


def test_thresholds_are_loaded_from_config():
    cfg = load_thresholds(force=True)
    assert cfg["checkin"]["allowed_window_minutes"] == 10
    assert cfg["checkin"]["missed_after_minutes"] == 30
    assert cfg["hybrid"]["rule_weight"] + cfg["hybrid"]["ml_weight"] == 1.0
    assert "min_duration_ratio" in cfg["patrol"]
    assert "max_accuracy_m" in cfg["gps"]
