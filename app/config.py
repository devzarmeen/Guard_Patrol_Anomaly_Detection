from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def config_dir() -> Path:
    return Path(os.getenv("CONFIG_PATH", PROJECT_ROOT / "config"))


def thresholds_path() -> Path:
    return config_dir() / "thresholds.yaml"

_thresholds_cache: dict[str, Any] | None = None


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in updates.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_thresholds(force: bool = False) -> dict[str, Any]:
    global _thresholds_cache
    if _thresholds_cache is not None and not force:
        return deepcopy(_thresholds_cache)

    path = thresholds_path()
    if not path.exists():
        raise FileNotFoundError(f"Threshold config not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    _thresholds_cache = data
    return deepcopy(data)


def save_thresholds(updates: dict[str, Any]) -> dict[str, Any]:
    current = load_thresholds(force=True)
    merged = _deep_merge(current, updates)
    path = thresholds_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(merged, handle, sort_keys=False)
    return load_thresholds(force=True)


def get_setting(path: str, default: Any = None) -> Any:
    data: Any = load_thresholds()
    for part in path.split("."):
        if not isinstance(data, dict) or part not in data:
            return default
        data = data[part]
    return data


def checkpoints_path() -> Path:
    return config_dir() / "checkpoints.yaml"


def load_checkpoints(force: bool = False) -> dict[str, Any]:
    path = checkpoints_path()
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("checkpoints", data) if isinstance(data, dict) else {}


def app_settings() -> dict[str, Any]:
    database_url = os.getenv("DATABASE_URL") or "sqlite:///./data/app.db"
    return {
        "app_name": os.getenv(
            "APP_NAME",
            "VigiloX Guard Patrol Anomaly Detection",
        ),
        "app_env": os.getenv("APP_ENV", "development"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "testing": os.getenv("TESTING", "false").lower() == "true",
        "database_url": database_url,
        "webhook_url": os.getenv("WEBHOOK_URL", ""),
        "smtp_host": os.getenv("SMTP_HOST", ""),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_username": os.getenv("SMTP_USERNAME", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "smtp_from": os.getenv("SMTP_FROM", os.getenv("SMTP_USERNAME", "")),
        "alert_email_to": os.getenv("ALERT_EMAIL_TO", ""),
        "scheduler_enabled": os.getenv("SCHEDULER_ENABLED", "true").lower()
        == "true",
    }
