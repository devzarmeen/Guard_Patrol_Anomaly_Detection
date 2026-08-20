from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from app.config import load_thresholds
from app.detection.types import GpsFeature
from app.geo import haversine_meters


def _as_dt(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def build_gps_features(
    rows: Sequence[dict[str, Any]],
    thresholds: dict[str, Any] | None = None,
    context_rows: Sequence[dict[str, Any]] | None = None,
) -> list[GpsFeature]:
    cfg = thresholds or load_thresholds()
    gps_cfg = cfg["gps"]
    sorted_rows = sorted(
        rows,
        key=lambda row: (str(row.get("guard_id")), _as_dt(row["timestamp"])),
    )

    features: list[GpsFeature] = []
    previous: dict[str, dict[str, Any]] = {}
    for row in context_rows or []:
        guard_id = str(row["guard_id"])
        previous[guard_id] = {
            "timestamp": _as_dt(row["timestamp"]),
            "lat": float(row["latitude"]),
            "lon": float(row["longitude"]),
        }

    for row in sorted_rows:
        guard_id = str(row["guard_id"])
        timestamp = _as_dt(row["timestamp"])
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        speed = float(row.get("speed") or row.get("speed_kmh") or 0.0)
        accuracy = row.get("accuracy") or row.get("gps_accuracy")
        distance_to_road = float(row.get("distance_to_road_m") or 0.0)

        time_gap = 0.0
        distance = 0.0
        prev = previous.get(guard_id)
        if prev is not None:
            time_gap = max(
                (timestamp - prev["timestamp"]).total_seconds(),
                0.0,
            )
            distance = haversine_meters(
                prev["lat"],
                prev["lon"],
                lat,
                lon,
            )
            if speed == 0.0 and time_gap > 0:
                speed = (distance / time_gap) * 3.6

        gps_jump = distance > float(gps_cfg["gps_jump_m"])
        long_gap = time_gap > float(gps_cfg["long_time_gap_seconds"])
        high_speed = speed > float(gps_cfg["high_speed_kmh"])
        large_road = distance_to_road > float(gps_cfg["large_road_deviation_m"])

        features.append(
            GpsFeature(
                guard_id=guard_id,
                timestamp=timestamp,
                latitude=lat,
                longitude=lon,
                speed_kmh=speed,
                time_gap_seconds=time_gap,
                distance_from_previous_m=distance,
                distance_to_road_m=distance_to_road,
                gps_accuracy=float(accuracy) if accuracy is not None else None,
                gps_jump=gps_jump,
                long_time_gap=long_gap,
                high_speed=high_speed,
                large_road_deviation=large_road,
            )
        )
        previous[guard_id] = {
            "timestamp": timestamp,
            "lat": lat,
            "lon": lon,
        }

    return features
