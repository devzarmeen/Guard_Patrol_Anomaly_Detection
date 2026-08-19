from __future__ import annotations

import json
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Any
from urllib import error, request

from sqlmodel import Session, select

from app.config import app_settings, load_thresholds
from app.models import AlertLog


def _should_alert(event: dict[str, Any], thresholds: dict[str, Any]) -> bool:
    alert_cfg = thresholds["alerting"]
    min_score = float(alert_cfg["min_hybrid_score"])
    min_levels = {str(level).lower() for level in alert_cfg["min_risk_levels"]}
    risk = str(event.get("event_risk_level", "")).lower()
    score = float(event.get("max_hybrid_score") or 0.0)
    return risk in min_levels or score >= min_score


def _send_email(subject: str, body: str, settings: dict[str, Any]) -> tuple[str, str | None]:
    if not settings["smtp_host"] or not settings["alert_email_to"]:
        return "skipped", "SMTP_HOST or ALERT_EMAIL_TO is not configured"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings["smtp_from"] or settings["smtp_username"]
    message["To"] = settings["alert_email_to"]
    message.set_content(body)

    with smtplib.SMTP(settings["smtp_host"], settings["smtp_port"], timeout=15) as smtp:
        smtp.starttls()
        if settings["smtp_username"]:
            smtp.login(settings["smtp_username"], settings["smtp_password"])
        smtp.send_message(message)
    return "sent", None


def _send_webhook(payload: dict[str, Any], settings: dict[str, Any]) -> tuple[str, str | None]:
    if not settings["webhook_url"]:
        return "skipped", "WEBHOOK_URL is not configured"

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        settings["webhook_url"],
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as response:
            if 200 <= response.status < 300:
                return "sent", None
            return "failed", f"Webhook status {response.status}"
    except error.URLError as exc:
        return "failed", str(exc)


def send_alerts_for_events(
    session: Session,
    events: list[dict[str, Any]],
    thresholds: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    cfg = thresholds or load_thresholds()
    settings = app_settings()
    results: list[dict[str, Any]] = []

    for event in events:
        if not _should_alert(event, cfg):
            continue

        event_key = (
            f"{event.get('guard_id')}:{event.get('event_id')}:"
            f"{event.get('start_time')}"
        )
        existing = session.exec(
            select(AlertLog).where(AlertLog.event_key == event_key)
        ).first()
        if existing and existing.status == "sent":
            continue

        subject = (
            f"[VigiloX] {event.get('event_risk_level')} patrol anomaly "
            f"for guard {event.get('guard_id')}"
        )
        body = (
            f"Guard: {event.get('guard_id')}\n"
            f"Risk: {event.get('event_risk_level')}\n"
            f"Score: {event.get('max_hybrid_score')}\n"
            f"Classification: {event.get('event_classification')}\n"
            f"Description: {event.get('description')}\n"
            f"Location: {event.get('latitude')}, {event.get('longitude')}\n"
            f"Window: {event.get('start_time')} → {event.get('end_time')}\n"
        )
        payload = {
            "source": "vigilox-guard-patrol",
            "event": event,
            "sent_at": datetime.utcnow().isoformat(),
        }

        if cfg["alerting"].get("email_enabled", True):
            status, err = _send_email(subject, body, settings)
            session.add(
                AlertLog(
                    event_key=event_key,
                    channel="email",
                    status=status,
                    message=subject,
                    error=err,
                )
            )
            results.append({"channel": "email", "status": status, "error": err})

        if cfg["alerting"].get("webhook_enabled", True):
            status, err = _send_webhook(payload, settings)
            session.add(
                AlertLog(
                    event_key=event_key,
                    channel="webhook",
                    status=status,
                    message="webhook",
                    error=err,
                )
            )
            results.append({"channel": "webhook", "status": status, "error": err})

    session.commit()
    return results
