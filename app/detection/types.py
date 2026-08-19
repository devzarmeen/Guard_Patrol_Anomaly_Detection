from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class GpsFeature(BaseModel):
    guard_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    speed_kmh: float = 0.0
    time_gap_seconds: float = 0.0
    distance_from_previous_m: float = 0.0
    distance_to_road_m: float = 0.0
    gps_accuracy: float | None = None
    gps_jump: bool = False
    long_time_gap: bool = False
    high_speed: bool = False
    large_road_deviation: bool = False
    rule_score: float = 0.0
    ml_score: float = 0.0
    hybrid_score: float = 0.0
    risk_level: str = "Low"
    is_anomaly: bool = False
    reasons: list[str] = []
    anomaly_type: str | None = None
    detection_method: str = "hybrid"


class DetectionResult(BaseModel):
    points: list[GpsFeature]
    events: list[dict[str, Any]] = []
    checkin_findings: list[dict[str, Any]] = []
    patrol_findings: list[dict[str, Any]] = []
