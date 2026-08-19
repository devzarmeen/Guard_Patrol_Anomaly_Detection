from datetime import datetime

from pydantic import BaseModel


class ActionableEventBase(BaseModel):
    guard_id: str
    patrol_id: str
    session_number: int

    event_id: int

    start_time: datetime
    end_time: datetime

    anomaly_points: int

    event_risk_level: str
    event_classification: str

    max_speed_kmh: float
    max_distance_jump_m: float
    max_distance_to_road_m: float
    max_hybrid_score: float

    description: str
    alert_status: str

    latitude: float
    longitude: float


class ActionableEventCreate(ActionableEventBase):
    pass


class ActionableEventUpdate(BaseModel):
    guard_id: str | None = None
    patrol_id: str | None = None
    session_number: int | None = None
    event_id: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    anomaly_points: int | None = None
    event_risk_level: str | None = None
    event_classification: str | None = None
    max_speed_kmh: float | None = None
    max_distance_jump_m: float | None = None
    max_distance_to_road_m: float | None = None
    max_hybrid_score: float | None = None
    description: str | None = None
    alert_status: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ActionableEventResponse(ActionableEventBase):
    id: int
