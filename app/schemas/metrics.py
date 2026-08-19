from pydantic import BaseModel


class MetricsResponse(BaseModel):
    total_anomalies: int
    total_actionable_events: int
    critical_anomalies: int
    high_anomalies: int
    medium_anomalies: int
    immediate_alerts: int
