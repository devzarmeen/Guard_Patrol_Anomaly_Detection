from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from app.database import session_scope
from app.models import AnomalyPoint
from app.schemas.anomaly import AnomalyCreate, AnomalyResponse, AnomalyUpdate

router = APIRouter(prefix="/api/anomalies", tags=["Anomalies"])


@router.post("", response_model=AnomalyResponse)
def create_anomaly(data: AnomalyCreate):
    with session_scope() as session:
        anomaly = AnomalyPoint(**data.model_dump())
        session.add(anomaly)
        session.commit()
        session.refresh(anomaly)
        return anomaly


@router.get("")
def get_anomalies(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=1000),
    risk_level: str | None = None,
    guard_id: str | None = None,
):
    with session_scope() as session:
        statement = select(AnomalyPoint)

        if risk_level:
            statement = statement.where(
                AnomalyPoint.final_risk_level == risk_level
            )

        if guard_id:
            statement = statement.where(AnomalyPoint.guard_id == guard_id)

        count_statement = select(func.count()).select_from(statement.subquery())
        total = session.exec(count_statement).one()

        offset = (page - 1) * limit
        statement = statement.offset(offset).limit(limit)
        anomalies = session.exec(statement).all()
        total_pages = (total + limit - 1) // limit if total > 0 else 0

        return {
            "data": anomalies,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }


@router.get("/{anomaly_id}", response_model=AnomalyResponse)
def get_anomaly(anomaly_id: int):
    with session_scope() as session:
        anomaly = session.get(AnomalyPoint, anomaly_id)
        if not anomaly:
            raise HTTPException(status_code=404, detail="Anomaly not found")
        return anomaly


@router.put("/{anomaly_id}", response_model=AnomalyResponse)
def update_anomaly(anomaly_id: int, data: AnomalyUpdate):
    with session_scope() as session:
        anomaly = session.get(AnomalyPoint, anomaly_id)
        if not anomaly:
            raise HTTPException(status_code=404, detail="Anomaly not found")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(anomaly, key, value)

        session.add(anomaly)
        session.commit()
        session.refresh(anomaly)
        return anomaly


@router.delete("/{anomaly_id}")
def delete_anomaly(anomaly_id: int):
    with session_scope() as session:
        anomaly = session.get(AnomalyPoint, anomaly_id)
        if not anomaly:
            raise HTTPException(status_code=404, detail="Anomaly not found")
        session.delete(anomaly)
        session.commit()
        return {"message": "Anomaly deleted successfully", "id": anomaly_id}
