from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import session_scope
from app.models import IncidentLabel
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.post("", response_model=IncidentResponse)
def create_incident(data: IncidentCreate):
    with session_scope() as session:
        existing = session.exec(
            select(IncidentLabel).where(IncidentLabel.event_id == data.event_id)
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Incident label already exists")
        label = IncidentLabel(
            **data.model_dump(),
            verification_timestamp=datetime.now(timezone.utc),
        )
        session.add(label)
        session.commit()
        session.refresh(label)
        return label


@router.get("", response_model=list[IncidentResponse])
def list_incidents():
    with session_scope() as session:
        return session.exec(select(IncidentLabel)).all()


@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: int, data: IncidentUpdate):
    with session_scope() as session:
        label = session.get(IncidentLabel, incident_id)
        if not label:
            raise HTTPException(status_code=404, detail="Incident not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(label, key, value)
        label.verification_timestamp = datetime.now(timezone.utc)
        session.add(label)
        session.commit()
        session.refresh(label)
        return label
