from datetime import datetime

from pydantic import BaseModel


class IncidentCreate(BaseModel):
    event_id: str
    guard_id: str
    anomaly_type: str
    is_incident: bool
    severity: str
    verified_by: str
    operator_decision: str | None = None
    notes: str | None = None


class IncidentUpdate(BaseModel):
    is_incident: bool | None = None
    severity: str | None = None
    verified_by: str | None = None
    operator_decision: str | None = None
    notes: str | None = None


class IncidentResponse(IncidentCreate):
    id: int
    verification_timestamp: datetime | None = None
