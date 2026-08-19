from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import app_settings
from app.database import create_tables
from app.routes.anomalies import router as anomalies_router
from app.routes.config import router as config_router
from app.routes.evaluation import router as evaluation_router
from app.routes.events import router as events_router
from app.routes.incidents import router as incidents_router
from app.routes.ingest import router as ingest_router
from app.routes.metrics import router as metrics_router
from app.services.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_tables()
    start_scheduler()
    yield
    shutdown_scheduler()


def create_app() -> FastAPI:
    settings = app_settings()
    application = FastAPI(
        title="VigiloX Guard Patrol Anomaly Detection API",
        version="1.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(anomalies_router)
    application.include_router(events_router)
    application.include_router(metrics_router)
    application.include_router(config_router)
    application.include_router(ingest_router)
    application.include_router(evaluation_router)
    application.include_router(incidents_router)

    @application.get("/")
    def root():
        return {
            "message": "VigiloX Guard Patrol Anomaly Detection API is running",
            "env": settings["app_env"],
        }

    @application.get("/health")
    def health():
        return {"status": "healthy"}

    return application


app = create_app()
