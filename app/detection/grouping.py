from __future__ import annotations

from typing import Any

from app.config import load_thresholds
from app.detection.types import GpsFeature


def group_actionable_events(
    points: list[GpsFeature],
    thresholds: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    cfg = thresholds or load_thresholds()
    max_gap = float(cfg["grouping"]["max_gap_seconds"])
    anomalies = [point for point in points if point.is_anomaly]
    anomalies.sort(key=lambda item: (item.guard_id, item.timestamp))

    events: list[dict[str, Any]] = []
    current: list[GpsFeature] = []

    def flush() -> None:
        if not current:
            return
        max_score = max(item.hybrid_score for item in current)
        risk = max(
            current,
            key=lambda item: item.hybrid_score,
        ).risk_level
        reasons = []
        for item in current:
            reasons.extend(item.reasons)
        unique_reasons = ", ".join(dict.fromkeys(reasons)) or "Anomaly cluster"
        if risk == "Critical":
            classification = "Strong Anomaly"
            alert_status = "Immediate Alert"
        elif risk == "High":
            classification = "Likely Anomaly"
            alert_status = "Immediate Alert"
        else:
            classification = "Monitor"
            alert_status = "Logged"

        events.append(
            {
                "guard_id": current[0].guard_id,
                "patrol_id": f"{current[0].guard_id}_PATROL",
                "session_number": 1,
                "event_id": len(events) + 1,
                "start_time": current[0].timestamp,
                "end_time": current[-1].timestamp,
                "anomaly_points": len(current),
                "event_risk_level": risk,
                "event_classification": classification,
                "max_speed_kmh": max(item.speed_kmh for item in current),
                "max_distance_jump_m": max(
                    item.distance_from_previous_m for item in current
                ),
                "max_distance_to_road_m": max(
                    item.distance_to_road_m for item in current
                ),
                "max_hybrid_score": max_score,
                "description": unique_reasons,
                "alert_status": alert_status,
                "latitude": current[0].latitude,
                "longitude": current[0].longitude,
            }
        )

    for point in anomalies:
        if not current:
            current = [point]
            continue
        gap = (point.timestamp - current[-1].timestamp).total_seconds()
        same_guard = point.guard_id == current[-1].guard_id
        if same_guard and gap <= max_gap:
            current.append(point)
        else:
            flush()
            current = [point]
    flush()
    return events
