from __future__ import annotations

from datetime import datetime
from typing import Any

from app.config import load_thresholds


def _as_dt(value: datetime | str | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def detect_patrols(
    rows: list[dict[str, Any]],
    now: datetime | None = None,
    thresholds: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    all_cfg = thresholds or load_thresholds()
    cfg = all_cfg["checkin"]
    patrol_cfg = all_cfg.get("patrol", {})
    missed_min = float(cfg["missed_after_minutes"])
    min_ratio = float(patrol_cfg.get("min_duration_ratio", 0.4))
    max_ratio = float(patrol_cfg.get("max_duration_ratio", 2.5))
    reference = now or datetime.utcnow()
    findings: list[dict[str, Any]] = []

    by_patrol: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_patrol.setdefault(str(row["patrol_id"]), []).append(row)

    for patrol_id, stops in by_patrol.items():
        ordered_expected = sorted(stops, key=lambda item: int(item["sequence"]))
        completed = [
            stop
            for stop in ordered_expected
            if _as_dt(stop.get("actual_time")) is not None
        ]
        completed_by_time = sorted(
            completed,
            key=lambda item: _as_dt(item["actual_time"]) or datetime.min,
        )

        for stop in ordered_expected:
            actual = _as_dt(stop.get("actual_time"))
            expected = _as_dt(stop.get("expected_time"))
            if actual is None and expected is not None:
                wait_minutes = (reference - expected).total_seconds() / 60.0
                if wait_minutes > missed_min:
                    findings.append(
                        {
                            "patrol_id": patrol_id,
                            "guard_id": stop.get("guard_id"),
                            "checkpoint_id": stop.get("checkpoint_id"),
                            "anomaly_type": "CHECKPOINT_MISSED",
                            "reasons": ["Expected checkpoint was not completed"],
                            "is_anomaly": True,
                        }
                    )

        completed_sequences = [int(stop["sequence"]) for stop in completed_by_time]
        if completed_sequences != sorted(completed_sequences):
            findings.append(
                {
                    "patrol_id": patrol_id,
                    "guard_id": ordered_expected[0].get("guard_id"),
                    "checkpoint_id": None,
                    "anomaly_type": "CHECKPOINT_OUT_OF_ORDER",
                    "reasons": ["Checkpoints were visited out of sequence"],
                    "is_anomaly": True,
                }
            )

        timed = [
            (_as_dt(stop.get("actual_time")), _as_dt(stop.get("expected_time")))
            for stop in ordered_expected
            if _as_dt(stop.get("actual_time")) and _as_dt(stop.get("expected_time"))
        ]
        if len(timed) >= 2:
            actual_duration = (timed[-1][0] - timed[0][0]).total_seconds()
            expected_duration = (timed[-1][1] - timed[0][1]).total_seconds()
            if expected_duration > 0:
                ratio = actual_duration / expected_duration
                if ratio < min_ratio or ratio > max_ratio:
                    findings.append(
                        {
                            "patrol_id": patrol_id,
                            "guard_id": ordered_expected[0].get("guard_id"),
                            "checkpoint_id": None,
                            "anomaly_type": "PATROL_DURATION_ANOMALY",
                            "reasons": ["Patrol duration differs significantly from expected"],
                            "is_anomaly": True,
                        }
                    )

    return findings
