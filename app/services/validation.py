from __future__ import annotations

from datetime import datetime
from typing import Any


def _as_dt(value: datetime | str | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def validate_gps_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not row.get("guard_id"):
        errors.append("guard_id is required")
    try:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        if not -90 <= lat <= 90:
            errors.append("latitude must be between -90 and 90")
        if not -180 <= lon <= 180:
            errors.append("longitude must be between -180 and 180")
    except (KeyError, TypeError, ValueError):
        errors.append("latitude and longitude must be valid numbers")
    try:
        _as_dt(row["timestamp"])
    except (KeyError, TypeError, ValueError):
        errors.append("timestamp must be a valid datetime")
    accuracy = row.get("accuracy")
    if accuracy is not None:
        try:
            if float(accuracy) < 0:
                errors.append("accuracy must be >= 0")
        except (TypeError, ValueError):
            errors.append("accuracy must be a number")
    return errors


def validate_checkin_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ("checkin_id", "guard_id", "site_id", "shift_id", "checkpoint_id")
    for field in required:
        if not row.get(field):
            errors.append(f"{field} is required")
    try:
        _as_dt(row["expected_time"])
    except (KeyError, TypeError, ValueError):
        errors.append("expected_time must be a valid datetime")
    if row.get("actual_time"):
        try:
            _as_dt(row["actual_time"])
        except (TypeError, ValueError):
            errors.append("actual_time must be a valid datetime")
    return errors
