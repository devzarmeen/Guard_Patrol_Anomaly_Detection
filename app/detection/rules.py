from __future__ import annotations

from typing import Any

from app.config import load_thresholds
from app.detection.types import GpsFeature


def _assign_rule_score(point: GpsFeature, gps_cfg: dict[str, Any]) -> tuple[float, list[str], str | None]:
    reasons: list[str] = []
    score = 0.0
    anomaly_type: str | None = None

    max_accuracy = float(gps_cfg.get("max_accuracy_m", 50))
    if point.gps_accuracy is not None and point.gps_accuracy > max_accuracy:
        reasons.append("GPS_DATA_ERROR")
        anomaly_type = "GPS_DATA_ERROR"
        score = max(score, 0.25)

    if point.speed_kmh > float(gps_cfg["extreme_speed_kmh"]):
        reasons.append("Extreme speed")
        anomaly_type = "ABNORMAL_SPEED"
        score = max(score, 0.50)
    elif point.speed_kmh > float(gps_cfg["very_high_speed_kmh"]):
        reasons.append("Very high speed")
        anomaly_type = "ABNORMAL_SPEED"
        score = max(score, 0.35)
    elif point.high_speed:
        reasons.append("High speed")
        anomaly_type = anomaly_type or "ABNORMAL_SPEED"
        score = max(score, 0.35)

    if point.distance_to_road_m > float(gps_cfg["extreme_road_deviation_m"]):
        reasons.append("Extreme route deviation")
        anomaly_type = "ROUTE_DEVIATION"
        score = max(score, 0.50)
    elif point.distance_to_road_m > float(gps_cfg["very_large_road_deviation_m"]):
        reasons.append("Large route deviation")
        anomaly_type = "ROUTE_DEVIATION"
        score = max(score, 0.35)
    elif point.large_road_deviation:
        reasons.append("Far from road")
        anomaly_type = anomaly_type or "ROUTE_DEVIATION"
        score = max(score, 0.25)

    if point.time_gap_seconds > float(gps_cfg["critical_time_gap_seconds"]):
        reasons.append("Critical time gap")
        anomaly_type = anomaly_type or "SUSPICIOUS_TIMING"
        score = max(score, 0.50)
    elif point.time_gap_seconds > float(gps_cfg["high_time_gap_seconds"]):
        reasons.append("Large time gap")
        anomaly_type = anomaly_type or "SUSPICIOUS_TIMING"
        score = max(score, 0.35)
    elif point.long_time_gap:
        reasons.append("Long time gap")
        anomaly_type = anomaly_type or "SUSPICIOUS_TIMING"
        score = max(score, 0.25)

    if point.gps_jump:
        reasons.append("Large distance jump")
        anomaly_type = anomaly_type or "GPS_DATA_ERROR"
        score = max(score, 0.50)

    if point.distance_from_previous_m > float(gps_cfg["route_deviation_m"]) and not point.gps_jump:
        reasons.append("Potential geofence / route deviation")
        anomaly_type = anomaly_type or "GEOFENCE_VIOLATION"
        score = max(score, 0.25)

    return score, reasons, anomaly_type


def _risk_from_score(score: float, risk_cfg: dict[str, Any]) -> str:
    if score >= float(risk_cfg["critical"]):
        return "Critical"
    if score >= float(risk_cfg["high"]):
        return "High"
    if score >= float(risk_cfg["medium"]):
        return "Medium"
    if score >= float(risk_cfg["low"]):
        return "Low"
    return "Low"


def detect_rule_based(
    points: list[GpsFeature],
    thresholds: dict[str, Any] | None = None,
) -> list[GpsFeature]:
    cfg = thresholds or load_thresholds()
    gps_cfg = cfg["gps"]
    hybrid_cfg = cfg["hybrid"]
    risk_cfg = cfg["risk"]
    cutoff = float(hybrid_cfg["anomaly_score_threshold"])

    scored: list[GpsFeature] = []
    for point in points:
        updated = point.model_copy(deep=True)
        score, reasons, anomaly_type = _assign_rule_score(updated, gps_cfg)
        updated.rule_score = score
        updated.hybrid_score = score
        updated.ml_score = 0.0
        updated.reasons = reasons
        updated.anomaly_type = anomaly_type
        updated.risk_level = _risk_from_score(score, risk_cfg)
        updated.is_anomaly = score >= cutoff or bool(reasons and score >= 0.35)
        updated.detection_method = "rule"
        scored.append(updated)
    return scored
