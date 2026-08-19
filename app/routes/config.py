from typing import Any

from fastapi import APIRouter

from app.config import load_thresholds, save_thresholds

router = APIRouter(prefix="/api/config", tags=["Configuration"])


@router.get("/thresholds")
def get_thresholds() -> dict[str, Any]:
    return load_thresholds(force=True)


@router.put("/thresholds")
def update_thresholds(updates: dict[str, Any]) -> dict[str, Any]:
    return save_thresholds(updates)
