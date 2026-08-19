from datetime import datetime

from pydantic import BaseModel


class AnomalyBase(BaseModel):
    guard_id: str
    timestamp: datetime

    latitude: float
    longitude: float

    speed_kmh: float
    time_gap_seconds: float
    distance_from_previous_m: float
    distance_to_road_m: float

    final_hybrid_score: float
    final_risk_level: str
    final_anomaly: bool

    anomaly_reason: str | None = None


class AnomalyCreate(AnomalyBase):
    pass


class AnomalyUpdate(BaseModel):
    guard_id: str | None = None
    timestamp: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    speed_kmh: float | None = None
    time_gap_seconds: float | None = None
    distance_from_previous_m: float | None = None
    distance_to_road_m: float | None = None
    final_hybrid_score: float | None = None
    final_risk_level: str | None = None
    final_anomaly: bool | None = None
    anomaly_reason: str | None = None


class AnomalyResponse(AnomalyBase):
    id: int
