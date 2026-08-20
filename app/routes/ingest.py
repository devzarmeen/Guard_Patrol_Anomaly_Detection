from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import session_scope
from app.models import CheckinEvent, GpsEvent, IncidentLabel, PatrolStop
from app.schemas.ingest import CheckinIngest, GpsIngest, IncidentIngest, PatrolIngest
from app.services.pipeline import ingest_sample_files, run_detection_pipeline
from app.services.validation import validate_checkin_row, validate_gps_row

router = APIRouter(prefix="/api", tags=["Ingest"])


@router.post("/ingest/gps")
def ingest_gps(payload: list[GpsIngest]):
    ingested = 0
    skipped = 0
    with session_scope() as session:
        for item in payload:
            errors = validate_gps_row(item.model_dump())
            if errors:
                raise HTTPException(status_code=422, detail=errors)
            exists = session.exec(
                select(GpsEvent).where(
                    GpsEvent.guard_id == item.guard_id,
                    GpsEvent.timestamp == item.timestamp,
                )
            ).first()
            if exists:
                skipped += 1
                continue
            session.add(GpsEvent(**item.model_dump(), processed=False))
            ingested += 1
        session.commit()
    return {"ingested": ingested, "skipped": skipped}


@router.post("/ingest/checkins")
def ingest_checkins(payload: list[CheckinIngest]):
    ingested = 0
    updated = 0
    with session_scope() as session:
        for item in payload:
            data = item.model_dump()
            errors = validate_checkin_row(data)
            if errors:
                raise HTTPException(status_code=422, detail=errors)
            exists = session.exec(
                select(CheckinEvent).where(
                    CheckinEvent.checkin_id == item.checkin_id
                )
            ).first()
            if exists:
                for key, value in data.items():
                    setattr(exists, key, value)
                exists.processed = False
                session.add(exists)
                updated += 1
                continue
            session.add(CheckinEvent(**data, processed=False))
            ingested += 1
        session.commit()
    return {"ingested": ingested, "updated": updated}


@router.post("/ingest/patrols")
def ingest_patrols(payload: list[PatrolIngest]):
    ingested = 0
    updated = 0
    with session_scope() as session:
        for item in payload:
            data = item.model_dump()
            exists = session.exec(
                select(PatrolStop).where(
                    PatrolStop.patrol_id == item.patrol_id,
                    PatrolStop.checkpoint_id == item.checkpoint_id,
                )
            ).first()
            if exists:
                for key, value in data.items():
                    setattr(exists, key, value)
                exists.processed = False
                session.add(exists)
                updated += 1
                continue
            session.add(PatrolStop(**data, processed=False))
            ingested += 1
        session.commit()
    return {"ingested": ingested, "updated": updated}


@router.post("/ingest/incidents")
def ingest_incidents(payload: list[IncidentIngest]):
    with session_scope() as session:
        for item in payload:
            session.add(IncidentLabel(**item.model_dump()))
        session.commit()
    return {"ingested": len(payload)}


@router.post("/ingest/sample")
def ingest_sample():
    with session_scope() as session:
        counts = ingest_sample_files(session)
    return {"ingested": counts}


@router.post("/pipeline/incremental")
def run_incremental():
    with session_scope() as session:
        return run_detection_pipeline(
            session,
            incremental=True,
            persist=True,
            send_alerts=True,
        )


@router.post("/pipeline/batch")
def run_batch(method: str = "hybrid"):
    with session_scope() as session:
        return run_detection_pipeline(
            session,
            incremental=False,
            persist=True,
            send_alerts=True,
            method=method,
        )
