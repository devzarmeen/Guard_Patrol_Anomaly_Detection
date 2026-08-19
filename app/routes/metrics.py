from fastapi import APIRouter
from sqlmodel import select

from app.database import session_scope
from app.models import ActionableEvent, AnomalyPoint
from app.schemas.metrics import MetricsResponse

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


@router.get("", response_model=MetricsResponse)
def get_metrics():
    with session_scope() as session:
        anomalies = session.exec(select(AnomalyPoint)).all()
        events = session.exec(select(ActionableEvent)).all()
        return {
            "total_anomalies": len(anomalies),
            "total_actionable_events": len(events),
            "critical_anomalies": sum(
                1 for item in anomalies if item.final_risk_level == "Critical"
            ),
            "high_anomalies": sum(
                1 for item in anomalies if item.final_risk_level == "High"
            ),
            "medium_anomalies": sum(
                1 for item in anomalies if item.final_risk_level == "Medium"
            ),
            "immediate_alerts": sum(
                1 for item in events if item.alert_status == "Immediate Alert"
            ),
        }
