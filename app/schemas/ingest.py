from datetime import datetime

from pydantic import BaseModel, Field


class GpsIngest(BaseModel):
    guard_id: str
    timestamp: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: float | None = Field(default=None, ge=0)
    speed: float | None = None
    heading: float | None = None


class CheckinIngest(BaseModel):
    checkin_id: str
    guard_id: str
    site_id: str
    shift_id: str
    checkpoint_id: str
    expected_time: datetime
    actual_time: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    gps_accuracy: float | None = None


class PatrolIngest(BaseModel):
    guard_id: str
    patrol_id: str
    checkpoint_id: str
    expected_time: datetime
    actual_time: datetime | None = None
    sequence: int
    route_id: str | None = None
    site_id: str | None = None


class IncidentIngest(BaseModel):
    event_id: str
    guard_id: str
    anomaly_type: str
    is_incident: bool
    severity: str
    verified_by: str
    operator_decision: str | None = None
    notes: str | None = None
