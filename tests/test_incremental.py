from datetime import datetime, timedelta

from sqlmodel import Session, select

import app.database as db
from app.models import GpsEvent


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
