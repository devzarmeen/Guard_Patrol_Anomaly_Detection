from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AnomalyPoint(SQLModel, table=True):
    __tablename__ = "anomaly_points"

    id: Optional[int] = Field(default=None, primary_key=True)

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

    anomaly_reason: Optional[str] = None


class ActionableEvent(SQLModel, table=True):
    __tablename__ = "actionable_events"

    id: Optional[int] = Field(default=None, primary_key=True)

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


class CheckinEvent(SQLModel, table=True):
    __tablename__ = "checkin_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    checkin_id: str = Field(index=True)
    guard_id: str = Field(index=True)
    site_id: str
    shift_id: str
    checkpoint_id: str
    expected_time: datetime
    actual_time: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy: Optional[float] = None
    status: str = "PENDING"
    processed: bool = False


class GpsEvent(SQLModel, table=True):
    __tablename__ = "gps_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    guard_id: str = Field(index=True)
    timestamp: datetime = Field(index=True)
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    processed: bool = False


class PatrolStop(SQLModel, table=True):
    __tablename__ = "patrol_stops"

    id: Optional[int] = Field(default=None, primary_key=True)
    guard_id: str
    patrol_id: str = Field(index=True)
    checkpoint_id: str
    expected_time: datetime
    actual_time: Optional[datetime] = None
    sequence: int
    route_id: Optional[str] = None
    site_id: Optional[str] = None
    processed: bool = False


class IncidentLabel(SQLModel, table=True):
    __tablename__ = "incident_labels"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str = Field(index=True)
    guard_id: str
    anomaly_type: str
    is_incident: bool
    severity: str
    verified_by: str
    operator_decision: Optional[str] = None
    notes: Optional[str] = None
    verification_timestamp: Optional[datetime] = None


class ProcessingCursor(SQLModel, table=True):
    __tablename__ = "processing_cursors"

    stream_name: str = Field(primary_key=True)
    last_timestamp: Optional[datetime] = None
    last_id: Optional[int] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AlertLog(SQLModel, table=True):
    __tablename__ = "alert_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_key: str
    channel: str
    status: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
