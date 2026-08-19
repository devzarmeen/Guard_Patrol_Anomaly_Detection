from app.routes.anomalies import router as anomalies_router
from app.routes.config import router as config_router
from app.routes.evaluation import router as evaluation_router
from app.routes.events import router as events_router
from app.routes.incidents import router as incidents_router
from app.routes.ingest import router as ingest_router
from app.routes.metrics import router as metrics_router

__all__ = [
    "anomalies_router",
    "events_router",
    "metrics_router",
    "config_router",
    "ingest_router",
    "evaluation_router",
    "incidents_router",
]
