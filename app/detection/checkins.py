from __future__ import annotations

from datetime import datetime
from typing import Any

from app.config import load_thresholds
from app.geo import haversine_meters


def _as_dt(value: datetime | str | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def classify_checkin(
    row: dict[str, Any],
    checkpoint: dict[str, Any] | None = None,
    now: datetime | None = None,
    thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = (thresholds or load_thresholds())["checkin"]
    expected = _as_dt(row["expected_time"])
    actual = _as_dt(row.get("actual_time"))
    reference = now or datetime.utcnow()
    window_min = float(cfg["allowed_window_minutes"])
    missed_min = float(cfg["missed_after_minutes"])
    max_accuracy = float(cfg["max_gps_accuracy_m"])
    radius = float(cfg["checkpoint_radius_m"])

    reasons: list[str] = []
    anomaly_type: str | None = None
    status = "NORMAL"
    delay_minutes: float | None = None

    if actual is None:
        wait_minutes = (reference - expected).total_seconds() / 60.0 if expected else 0.0
        if wait_minutes > missed_min:
            status = "MISSED"
            anomaly_type = "CHECKIN_MISSED"
            reasons.append("No check-in within configured waiting period")
        else:
            status = "PENDING"
    else:
        delay_minutes = (actual - expected).total_seconds() / 60.0 if expected else 0.0
        if delay_minutes > window_min:
            status = "LATE"
            anomaly_type = "CHECKIN_LATE"
            reasons.append(f"Check-in delay of {delay_minutes:.1f} minutes")

    accuracy = row.get("gps_accuracy")
    if accuracy is not None and float(accuracy) > max_accuracy:
        reasons.append("GPS accuracy exceeds configured limit")
        if status == "NORMAL":
            status = "INVALID"
        anomaly_type = anomaly_type or "GPS_DATA_ERROR"

    lat = row.get("latitude")
    lon = row.get("longitude")
    if checkpoint and lat is not None and lon is not None:
        distance = haversine_meters(
            float(lat),
            float(lon),
            float(checkpoint["latitude"]),
            float(checkpoint["longitude"]),
        )
        if distance > radius:
            reasons.append("Check-in is outside checkpoint proximity radius")
            if status == "NORMAL":
                status = "INVALID"
            anomaly_type = anomaly_type or "ROUTE_DEVIATION"

    return {
        "checkin_id": row.get("checkin_id"),
        "guard_id": row.get("guard_id"),
        "checkpoint_id": row.get("checkpoint_id"),
        "status": status,
        "delay_minutes": delay_minutes,
        "anomaly_type": anomaly_type,
        "reasons": reasons,
        "is_anomaly": status in {"LATE", "MISSED", "INVALID"},
    }


def detect_checkins(
    rows: list[dict[str, Any]],
    checkpoints: dict[str, dict[str, Any]] | None = None,
    now: datetime | None = None,
    thresholds: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    findings = []
    for row in rows:
        checkpoint = None
        if checkpoints:
            checkpoint = checkpoints.get(str(row.get("checkpoint_id")))
        findings.append(classify_checkin(row, checkpoint, now, thresholds))
    return findings
