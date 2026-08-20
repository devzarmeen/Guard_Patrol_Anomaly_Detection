from datetime import datetime, timedelta

from sqlmodel import Session, select

import app.database as db
from app.models import CheckinEvent, GpsEvent, PatrolStop


def test_incremental_processing_marks_new_gps_only(client):
    first = datetime(2026, 8, 13, 8, 30)
    payload = [
        {
            "guard_id": "G001",
            "timestamp": first.isoformat(),
            "latitude": 51.5074,
            "longitude": -0.1278,
            "accuracy": 8,
            "speed": 3.2,
        },
        {
            "guard_id": "G001",
            "timestamp": (first + timedelta(seconds=5)).isoformat(),
            "latitude": 51.52,
            "longitude": -0.14,
            "accuracy": 12,
            "speed": 80,
        },
    ]
    response = client.post("/api/ingest/gps", json=payload)
    assert response.status_code == 200
    assert response.json()["ingested"] == 2

    first_run = client.post("/api/pipeline/incremental")
    assert first_run.status_code == 200
    assert first_run.json()["gps_points"] == 2

    with Session(db.engine) as session:
        remaining = session.exec(
            select(GpsEvent).where(GpsEvent.processed == False)  # noqa: E712
        ).all()
        assert remaining == []

    second_run = client.post("/api/pipeline/incremental")
    assert second_run.json()["gps_points"] == 0


def test_incremental_gps_uses_previous_point_as_context(client):
    first = datetime(2026, 8, 13, 8, 30)
    first_ingest = client.post(
        "/api/ingest/gps",
        json=[
            {
                "guard_id": "G001",
                "timestamp": first.isoformat(),
                "latitude": 51.5074,
                "longitude": -0.1278,
                "accuracy": 8,
                "speed": 3.2,
            }
        ],
    )
    assert first_ingest.status_code == 200
    client.post("/api/pipeline/incremental")

    second = client.post(
        "/api/ingest/gps",
        json=[
            {
                "guard_id": "G001",
                "timestamp": (first + timedelta(seconds=5)).isoformat(),
                "latitude": 51.52,
                "longitude": -0.14,
                "accuracy": 12,
                "speed": 80,
            }
        ],
    )
    assert second.json()["ingested"] == 1
    result = client.post("/api/pipeline/incremental")
    assert result.status_code == 200
    assert result.json()["gps_points"] == 1
    with Session(db.engine) as session:
        remaining = session.exec(
            select(GpsEvent).where(GpsEvent.processed == False)  # noqa: E712
        ).all()
        assert remaining == []


def test_incremental_checkin_upsert_and_pending_wait(client):
    expected = datetime.utcnow() + timedelta(minutes=5)
    pending = {
        "checkin_id": "CI-100",
        "guard_id": "G001",
        "site_id": "SITE_001",
        "shift_id": "SHIFT_A",
        "checkpoint_id": "CP001",
        "expected_time": expected.isoformat(),
        "actual_time": None,
        "latitude": 51.5074,
        "longitude": -0.1278,
        "gps_accuracy": 8,
    }
    created = client.post("/api/ingest/checkins", json=[pending])
    assert created.status_code == 200
    assert created.json()["ingested"] == 1

    first_run = client.post("/api/pipeline/incremental")
    assert first_run.status_code == 200
    with Session(db.engine) as session:
        row = session.exec(
            select(CheckinEvent).where(CheckinEvent.checkin_id == "CI-100")
        ).first()
        assert row is not None
        assert row.processed is False

    updated = client.post(
        "/api/ingest/checkins",
        json=[
            {
                **pending,
                "actual_time": (expected + timedelta(minutes=12)).isoformat(),
            }
        ],
    )
    assert updated.json()["updated"] == 1
    second_run = client.post("/api/pipeline/incremental")
    assert second_run.status_code == 200
    types = {
        item["anomaly_type"]
        for item in second_run.json()["checkin_findings"]
        if item.get("is_anomaly")
    }
    assert "CHECKIN_LATE" in types
    with Session(db.engine) as session:
        row = session.exec(
            select(CheckinEvent).where(CheckinEvent.checkin_id == "CI-100")
        ).first()
        assert row is not None
        assert row.processed is True


def test_incremental_patrol_upsert(client):
    expected = datetime.utcnow() + timedelta(minutes=5)
    payload = {
        "guard_id": "G001",
        "patrol_id": "P-100",
        "checkpoint_id": "CP001",
        "expected_time": expected.isoformat(),
        "actual_time": None,
        "sequence": 1,
        "route_id": "R001",
        "site_id": "SITE_001",
    }
    created = client.post("/api/ingest/patrols", json=[payload])
    assert created.json()["ingested"] == 1
    client.post("/api/pipeline/incremental")
    with Session(db.engine) as session:
        row = session.exec(
            select(PatrolStop).where(PatrolStop.patrol_id == "P-100")
        ).first()
        assert row is not None
        assert row.processed is False

    updated = client.post(
        "/api/ingest/patrols",
        json=[
            {
                **payload,
                "actual_time": expected.isoformat(),
            }
        ],
    )
    assert updated.json()["updated"] == 1
    client.post("/api/pipeline/incremental")
    with Session(db.engine) as session:
        row = session.exec(
            select(PatrolStop).where(PatrolStop.patrol_id == "P-100")
        ).first()
        assert row is not None
        assert row.processed is True
