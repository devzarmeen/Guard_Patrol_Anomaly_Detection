from __future__ import annotations

import json
import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Any
from urllib import error, request

from sqlmodel import Session, select

from app.config import app_settings, load_thresholds
from app.models import AlertLog

logger = logging.getLogger(__name__)


def _json_default(value: Any) -> Any:
    """Convert non-JSON values to serializable values."""
    if isinstance(value, datetime):
        return value.isoformat()

    return str(value)


def _format_datetime(value: Any) -> str:
    """Convert datetime values to ISO-8601 strings."""
    if isinstance(value, datetime):
        return value.isoformat()

    if value is None:
        return ""

    return str(value)


def _should_alert(
    event: dict[str, Any],
    thresholds: dict[str, Any],
) -> bool:
    """Check whether an event meets the configured alert criteria."""
    alert_cfg = thresholds["alerting"]

    min_score = float(
        alert_cfg["min_hybrid_score"]
    )

    min_levels = {
        str(level).lower()
        for level in alert_cfg["min_risk_levels"]
    }

    risk = str(
        event.get("event_risk_level", "")
    ).lower()

    score = float(
        event.get("max_hybrid_score") or 0.0
    )

    return (
        risk in min_levels
        or score >= min_score
    )


def _latest_log(
    session: Session,
    event_key: str,
    channel: str,
) -> AlertLog | None:
    """Get the latest alert log for an event/channel."""
    return session.exec(
        select(AlertLog)
        .where(
            AlertLog.event_key == event_key,
            AlertLog.channel == channel,
        )
        .order_by(AlertLog.id.desc())
    ).first()


def _send_email(
    subject: str,
    body: str,
    settings: dict[str, Any],
) -> tuple[str, str | None]:
    """Send an email alert."""

    if (
        not settings["smtp_host"]
        or not settings["alert_email_to"]
    ):
        return (
            "skipped",
            "SMTP_HOST or ALERT_EMAIL_TO is not configured",
        )

    message = EmailMessage()

    message["Subject"] = subject

    message["From"] = (
        settings["smtp_from"]
        or settings["smtp_username"]
    )

    message["To"] = settings["alert_email_to"]

    message.set_content(body)

    try:
        if settings.get("smtp_use_ssl"):
            client: smtplib.SMTP = smtplib.SMTP_SSL(
                settings["smtp_host"],
                settings["smtp_port"],
                timeout=15,
            )
        else:
            client = smtplib.SMTP(
                settings["smtp_host"],
                settings["smtp_port"],
                timeout=15,
            )

        with client as smtp:

            if (
                settings.get("smtp_use_tls")
                and not settings.get("smtp_use_ssl")
            ):
                smtp.starttls()

            if settings["smtp_username"]:
                smtp.login(
                    settings["smtp_username"],
                    settings["smtp_password"],
                )

            smtp.send_message(message)

        return "sent", None

    except (
        smtplib.SMTPException,
        OSError,
        TimeoutError,
        ValueError,
    ) as exc:

        logger.warning(
            "Alert email failed: %s",
            exc,
        )

        return "failed", str(exc)


def _send_webhook(
    payload: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[str, str | None]:
    """Send alert payload to the configured webhook."""

    if not settings["webhook_url"]:
        return (
            "skipped",
            "WEBHOOK_URL is not configured",
        )

    try:
        data = json.dumps(
            payload,
            default=_json_default,
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
        }

        if settings.get("webhook_token"):
            headers["Authorization"] = (
                f"Bearer {settings['webhook_token']}"
            )

        req = request.Request(
            settings["webhook_url"],
            data=data,
            headers=headers,
            method="POST",
        )

        timeout = int(
            settings.get(
                "webhook_timeout_seconds"
            )
            or 15
        )

        with request.urlopen(
            req,
            timeout=timeout,
        ) as response:

            if 200 <= response.status < 300:
                return "sent", None

            return (
                "failed",
                f"Webhook status {response.status}",
            )

    except error.HTTPError as exc:

        logger.warning(
            "Alert webhook HTTP error: %s",
            exc,
        )

        return (
            "failed",
            f"Webhook status {exc.code}",
        )

    except (
        error.URLError,
        TimeoutError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:

        logger.warning(
            "Alert webhook failed: %s",
            exc,
        )

        return "failed", str(exc)


def _record_alert(
    session: Session,
    event_key: str,
    channel: str,
    status: str,
    message: str,
    error_message: str | None,
) -> dict[str, Any]:
    """Save alert result in the database."""

    session.add(
        AlertLog(
            event_key=event_key,
            channel=channel,
            status=status,
            message=message,
            error=error_message,
        )
    )

    return {
        "channel": channel,
        "status": status,
        "error": error_message,
    }


def send_alerts_for_events(
    session: Session,
    events: list[dict[str, Any]],
    thresholds: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Send email and webhook alerts for anomaly events."""

    cfg = thresholds or load_thresholds()

    settings = app_settings()

    results: list[dict[str, Any]] = []

    for event in events:

        # ---------------------------------------------------------
        # Check alert threshold
        # ---------------------------------------------------------
        if not _should_alert(event, cfg):
            continue

        # ---------------------------------------------------------
        # Unique event key
        # ---------------------------------------------------------
        event_key = (
            f"{event.get('guard_id')}:"
            f"{event.get('event_id')}:"
            f"{event.get('start_time')}"
        )

        # ---------------------------------------------------------
        # Event values
        # ---------------------------------------------------------
        guard_id = event.get("guard_id")

        risk_level = event.get(
            "event_risk_level"
        )

        hybrid_score = event.get(
            "max_hybrid_score"
        )

        classification = event.get(
            "event_classification"
        )

        description = event.get(
            "description"
        )

        latitude = event.get(
            "latitude"
        )

        longitude = event.get(
            "longitude"
        )

        start_time = _format_datetime(
            event.get("start_time")
        )

        end_time = _format_datetime(
            event.get("end_time")
        )

        # ---------------------------------------------------------
        # Email subject
        # ---------------------------------------------------------
        subject = (
            f"[VigiloX] {risk_level} patrol anomaly "
            f"for guard {guard_id}"
        )

        # ---------------------------------------------------------
        # Email body
        # ---------------------------------------------------------
        body = (
            f"Guard: {guard_id}\n"
            f"Risk: {risk_level}\n"
            f"Score: {hybrid_score}\n"
            f"Classification: {classification}\n"
            f"Description: {description}\n"
            f"Location: {latitude}, {longitude}\n"
            f"Window: {start_time} → {end_time}\n"
        )

        # ---------------------------------------------------------
        # Slack webhook text
        # ---------------------------------------------------------
        slack_text = (
            "🚨 *VigiloX Guard Patrol Anomaly*\n\n"
            f"*Guard:* {guard_id}\n"
            f"*Risk:* {risk_level}\n"
            f"*Hybrid Score:* {hybrid_score}\n"
            f"*Classification:* {classification}\n"
            f"*Description:* {description}\n"
            f"*Location:* {latitude}, {longitude}\n"
            f"*Window:* {start_time} → {end_time}"
        )

        # ---------------------------------------------------------
        # Webhook payload
        #
        # Keep event values unchanged so datetime objects are
        # serialized by _json_default() into ISO format.
        # ---------------------------------------------------------
        payload = {
            "text": slack_text,
            "event": event,
            "sent_at": datetime.utcnow(),
        }

        # =========================================================
        # EMAIL ALERT
        # =========================================================
        if cfg["alerting"].get(
            "email_enabled",
            True,
        ):

            existing = _latest_log(
                session,
                event_key,
                "email",
            )

            email_unconfigured = (
                not settings["smtp_host"]
                or not settings["alert_email_to"]
            )

            # Already successfully sent
            if (
                existing
                and existing.status == "sent"
            ):
                pass

            # Already skipped because configuration is missing
            elif (
                existing
                and existing.status == "skipped"
                and email_unconfigured
            ):
                pass

            else:

                status, err = _send_email(
                    subject,
                    body,
                    settings,
                )

                results.append(
                    _record_alert(
                        session,
                        event_key,
                        "email",
                        status,
                        subject,
                        err,
                    )
                )

        # =========================================================
        # WEBHOOK / SLACK ALERT
        # =========================================================
        if cfg["alerting"].get(
            "webhook_enabled",
            True,
        ):

            existing = _latest_log(
                session,
                event_key,
                "webhook",
            )

            webhook_unconfigured = (
                not settings["webhook_url"]
            )

            # Already successfully sent
            if (
                existing
                and existing.status == "sent"
            ):
                pass

            # Already skipped because configuration is missing
            elif (
                existing
                and existing.status == "skipped"
                and webhook_unconfigured
            ):
                pass

            else:

                status, err = _send_webhook(
                    payload,
                    settings,
                )

                results.append(
                    _record_alert(
                        session,
                        event_key,
                        "webhook",
                        status,
                        "slack_webhook",
                        err,
                    )
                )

    # -------------------------------------------------------------
    # Commit alert logs
    # -------------------------------------------------------------
    session.commit()

    return results