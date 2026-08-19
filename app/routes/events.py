from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import session_scope
from app.models import ActionableEvent
from app.schemas.event import (
    ActionableEventCreate,
    ActionableEventResponse,
    ActionableEventUpdate,
)

router = APIRouter(prefix="/api/actionable-events", tags=["Actionable Events"])


@router.post("", response_model=ActionableEventResponse)
def create_actionable_event(data: ActionableEventCreate):
    with session_scope() as session:
        event = ActionableEvent(**data.model_dump())
        session.add(event)
        session.commit()
        session.refresh(event)
        return event


@router.get("", response_model=list[ActionableEventResponse])
def get_actionable_events(
    event_classification: str | None = None,
    alert_status: str | None = None,
):
    with session_scope() as session:
        statement = select(ActionableEvent)
        if event_classification:
            statement = statement.where(
                ActionableEvent.event_classification == event_classification
            )
        if alert_status:
            statement = statement.where(
                ActionableEvent.alert_status == alert_status
            )
        return session.exec(statement).all()


@router.get("/{event_id}", response_model=ActionableEventResponse)
def get_actionable_event(event_id: int):
    with session_scope() as session:
        event = session.get(ActionableEvent, event_id)
        if not event:
            raise HTTPException(
                status_code=404,
                detail="Actionable event not found",
            )
        return event


@router.put("/{event_id}", response_model=ActionableEventResponse)
def update_actionable_event(event_id: int, data: ActionableEventUpdate):
    with session_scope() as session:
        event = session.get(ActionableEvent, event_id)
        if not event:
            raise HTTPException(
                status_code=404,
                detail="Actionable event not found",
            )
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(event, key, value)
        session.add(event)
        session.commit()
        session.refresh(event)
        return event


@router.delete("/{event_id}")
def delete_actionable_event(event_id: int):
    with session_scope() as session:
        event = session.get(ActionableEvent, event_id)
        if not event:
            raise HTTPException(
                status_code=404,
                detail="Actionable event not found",
            )
        session.delete(event)
        session.commit()
        return {
            "message": "Actionable event deleted successfully",
            "id": event_id,
        }
