from datetime import datetime, timedelta

from app.services.validation import validate_checkin_row, validate_gps_row


def test_gps_validation_rejects_invalid_coordinates():
    errors = validate_gps_row(
        {
            "guard_id": "G001",
            "timestamp": datetime(2026, 8, 13, 8, 30),
            "latitude": 120,
            "longitude": -0.12,
        }
    )
    assert errors


def test_checkin_validation_requires_expected_time():
    errors = validate_checkin_row(
        {
            "checkin_id": "CI1",
            "guard_id": "G001",
            "site_id": "SITE001",
            "shift_id": "SHIFT001",
            "checkpoint_id": "CP001",
        }
    )
    assert "expected_time must be a valid datetime" in errors


def test_gps_ingest_rejects_invalid_payload(client):
    response = client.post(
        "/api/ingest/gps",
        json=[
            {
                "guard_id": "G001",
                "timestamp": (datetime(2026, 8, 13, 8, 30) + timedelta()).isoformat(),
                "latitude": 91,
                "longitude": 0,
            }
        ],
    )
    assert response.status_code == 422
