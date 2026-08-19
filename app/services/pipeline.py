from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from app.config import PROJECT_ROOT, load_checkpoints, load_thresholds
from app.detection.checkins import detect_checkins
from app.detection.features import build_gps_features
from app.detection.grouping import group_actionable_events
from app.detection.hybrid import detect_hybrid
from app.detection.isolation_forest import detect_isolation_forest
from app.detection.patrols import detect_patrols
from app.detection.rules import detect_rule_based
from app.detection.evaluation import compare_methods
from app.evaluation.metrics import compare_methods
from app.models import (
    ActionableEvent,
    AnomalyPoint,
    CheckinEvent,
    GpsEvent,
    IncidentLabel,
    PatrolStop,
    ProcessingCursor,
)
from app.services.alerting import send_alerts_for_events


def _row_from_model(model: Any) -> dict[str, Any]:
    return model.model_dump()


def load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def ingest_sample_files(session: Session) -> dict[str, int]:
    sample_dir = PROJECT_ROOT / "data" / "sample"

    counts = {
        "checkins": 0,
        "gps": 0,
        "patrols": 0,
        "incidents": 0,
    }

    # =========================================================
    # CHECK-IN DATA
    # =========================================================

    checkins_path = sample_dir / "checkins_sample.csv"

    if checkins_path.exists():
        for row in load_csv(checkins_path):
            exists = session.exec(
                select(CheckinEvent).where(
                    CheckinEvent.checkin_id == row["checkin_id"]
                )
            ).first()

            if exists:
                continue

            session.add(
                CheckinEvent(
                    checkin_id=row["checkin_id"],
                    guard_id=row["guard_id"],
                    site_id=row["site_id"],
                    shift_id=row["shift_id"],
                    checkpoint_id=row["checkpoint_id"],
                    expected_time=datetime.fromisoformat(
                        row["expected_time"]
                    ),
                    actual_time=(
                        datetime.fromisoformat(row["actual_time"])
                        if row.get("actual_time")
                        else None
                    ),
                    latitude=(
                        float(row["latitude"])
                        if row.get("latitude")
                        else None
                    ),
                    longitude=(
                        float(row["longitude"])
                        if row.get("longitude")
                        else None
                    ),
                    gps_accuracy=(
                        float(row["gps_accuracy"])
                        if row.get("gps_accuracy")
                        else None
                    ),
                    status=row.get("status") or "PENDING",
                )
            )

            counts["checkins"] += 1

    # =========================================================
    # GPS DATA
    # =========================================================

    gps_path = sample_dir / "gps.csv"

    if gps_path.exists():
        for row in load_csv(gps_path):
            ts = datetime.fromisoformat(row["timestamp"])

            exists = session.exec(
                select(GpsEvent).where(
                    GpsEvent.guard_id == row["guard_id"],
                    GpsEvent.timestamp == ts,
                    GpsEvent.latitude == float(row["latitude"]),
                    GpsEvent.longitude == float(row["longitude"]),
                )
            ).first()

            if exists:
                continue

            session.add(
                GpsEvent(
                    guard_id=row["guard_id"],
                    timestamp=ts,
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    accuracy=(
                        float(row["accuracy"])
                        if row.get("accuracy")
                        else None
                    ),
                    speed=(
                        float(row["speed"])
                        if row.get("speed")
                        else None
                    ),
                    heading=(
                        float(row["heading"])
                        if row.get("heading")
                        else None
                    ),
                )
            )

            counts["gps"] += 1

    # =========================================================
    # PATROL DATA
    # =========================================================

    patrols_path = sample_dir / "patrols.csv"

    if patrols_path.exists():
        for row in load_csv(patrols_path):
            exists = session.exec(
                select(PatrolStop).where(
                    PatrolStop.patrol_id == row["patrol_id"],
                    PatrolStop.checkpoint_id == row["checkpoint_id"],
                )
            ).first()

            if exists:
                continue

            session.add(
                PatrolStop(
                    guard_id=row["guard_id"],
                    patrol_id=row["patrol_id"],
                    checkpoint_id=row["checkpoint_id"],
                    expected_time=datetime.fromisoformat(
                        row["expected_time"]
                    ),
                    actual_time=(
                        datetime.fromisoformat(row["actual_time"])
                        if row.get("actual_time")
                        else None
                    ),
                    sequence=int(row["sequence"]),
                    route_id=row.get("route_id"),
                    site_id=row.get("site_id"),
                )
            )

            counts["patrols"] += 1

    # =========================================================
    # INCIDENT DATA
    # =========================================================

    incidents_path = sample_dir / "incidents.csv"

    if incidents_path.exists():
        for row in load_csv(incidents_path):
            exists = session.exec(
                select(IncidentLabel).where(
                    IncidentLabel.event_id == row["event_id"]
                )
            ).first()

            if exists:
                continue

            session.add(
                IncidentLabel(
                    event_id=row["event_id"],
                    guard_id=row["guard_id"],
                    anomaly_type=row["anomaly_type"],
                    is_incident=(
                        str(row["is_incident"]).lower() == "true"
                    ),
                    severity=row["severity"],
                    verified_by=row["verified_by"],
                )
            )

            counts["incidents"] += 1

    session.commit()

    return counts


def _gps_rows(
    session: Session,
    incremental: bool,
) -> list[dict[str, Any]]:

    statement = select(GpsEvent)

    if incremental:
        statement = statement.where(
            GpsEvent.processed == False
        )  # noqa: E712

    rows = session.exec(statement).all()

    return [_row_from_model(row) for row in rows]


def persist_detection(
    session: Session,
    points: list[Any],
    events: list[dict[str, Any]],
) -> None:

    # =========================================================
    # PERSIST ANOMALY POINTS
    # =========================================================

    for point in points:

        if not point.is_anomaly:
            continue

        # Strong duplicate check:
        # guard + timestamp + latitude + longitude
        exists = session.exec(
            select(AnomalyPoint).where(
                AnomalyPoint.guard_id == point.guard_id,
                AnomalyPoint.timestamp == point.timestamp,
                AnomalyPoint.latitude == point.latitude,
                AnomalyPoint.longitude == point.longitude,
            )
        ).first()

        if exists:
            continue

        session.add(
            AnomalyPoint(
                guard_id=point.guard_id,
                timestamp=point.timestamp,
                latitude=point.latitude,
                longitude=point.longitude,
                speed_kmh=point.speed_kmh,
                time_gap_seconds=point.time_gap_seconds,
                distance_from_previous_m=point.distance_from_previous_m,
                distance_to_road_m=point.distance_to_road_m,
                final_hybrid_score=point.hybrid_score,
                final_risk_level=point.risk_level,
                final_anomaly=point.is_anomaly,
                anomaly_reason=(
                    f"[{point.detection_method}] "
                    + ", ".join(point.reasons)
                    if point.reasons
                    else point.detection_method
                ),
            )
        )

    # =========================================================
    # PERSIST ACTIONABLE EVENTS
    # =========================================================

    for event in events:

        exists = session.exec(
            select(ActionableEvent).where(
                ActionableEvent.guard_id == event["guard_id"],
                ActionableEvent.start_time == event["start_time"],
                ActionableEvent.description == event["description"],
            )
        ).first()

        if exists:
            continue

        session.add(
            ActionableEvent(**event)
        )

    session.commit()


def _mark_processed(
    session: Session,
    incremental: bool,
) -> None:

    if not incremental:
        return

    # =========================================================
    # MARK SOURCE DATA AS PROCESSED
    # =========================================================

    for model in (
        GpsEvent,
        CheckinEvent,
        PatrolStop,
    ):

        rows = session.exec(
            select(model).where(
                model.processed == False
            )
        ).all()  # noqa: E712

        for row in rows:
            row.processed = True
            session.add(row)

    # =========================================================
    # PROCESSING STATE / CHECKPOINT
    # =========================================================

    processing_state = session.get(
        ProcessingCursor,
        "gps",
    )

    if processing_state is None:

        processing_state = ProcessingCursor(
            stream_name="gps",
            updated_at=datetime.utcnow(),
        )

    processing_state.last_timestamp = datetime.utcnow()
    processing_state.updated_at = datetime.utcnow()

    session.add(processing_state)

    session.commit()


def _finding_events(
    findings: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    event_offset: int,
) -> list[dict[str, Any]]:

    by_id = {
        str(row.get("checkin_id") or ""): row
        for row in source_rows
    }

    events: list[dict[str, Any]] = []

    high_types = {
        "CHECKIN_MISSED",
        "CHECKPOINT_MISSED",
        "GEOFENCE_VIOLATION",
    }

    for finding in findings:

        if not finding.get("is_anomaly"):
            continue

        anomaly_type = str(
            finding.get("anomaly_type")
            or "ANOMALY"
        )

        risk = (
            "High"
            if anomaly_type in high_types
            else "Medium"
        )

        source = by_id.get(
            str(finding.get("checkin_id") or ""),
            {},
        )

        lat = (
            source.get("latitude")
            if source.get("latitude") is not None
            else 0.0
        )

        lon = (
            source.get("longitude")
            if source.get("longitude") is not None
            else 0.0
        )

        timestamp = (
            source.get("actual_time")
            or source.get("expected_time")
            or datetime.utcnow()
        )

        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )

        events.append(
            {
                "guard_id": (
                    finding.get("guard_id")
                    or "UNKNOWN"
                ),
                "patrol_id": str(
                    finding.get("patrol_id")
                    or "CHECKIN"
                ),
                "session_number": 1,
                "event_id": (
                    event_offset
                    + len(events)
                    + 1
                ),
                "start_time": timestamp,
                "end_time": timestamp,
                "anomaly_points": 1,
                "event_risk_level": risk,
                "event_classification": anomaly_type,
                "max_speed_kmh": 0.0,
                "max_distance_jump_m": 0.0,
                "max_distance_to_road_m": 0.0,
                "max_hybrid_score": (
                    0.7
                    if risk == "High"
                    else 0.4
                ),
                "description": "; ".join(
                    finding.get("reasons")
                    or [anomaly_type]
                ),
                "alert_status": (
                    "Immediate Alert"
                    if risk == "High"
                    else "Logged"
                ),
                "latitude": float(lat or 0.0),
                "longitude": float(lon or 0.0),
            }
        )

    return events


def run_detection_pipeline(
    session: Session,
    incremental: bool = False,
    persist: bool = True,
    send_alerts: bool = True,
    method: str = "hybrid",
) -> dict[str, Any]:

    thresholds = load_thresholds()
    checkpoints = load_checkpoints()

    gps_rows = _gps_rows(
        session,
        incremental,
    )

    checkin_rows = [
        _row_from_model(row)
        for row in session.exec(
            select(CheckinEvent)
        ).all()
    ]

    patrol_rows = [
        _row_from_model(row)
        for row in session.exec(
            select(PatrolStop)
        ).all()
    ]

    # =========================================================
    # GPS FEATURES
    # =========================================================

    features = build_gps_features(
        gps_rows,
        thresholds,
    )

    # =========================================================
    # DETECTION METHODS
    # =========================================================

    detectors = {
        "rule": detect_rule_based,
        "isolation_forest": detect_isolation_forest,
        "hybrid": detect_hybrid,
    }

    detector = detectors.get(
        method,
        detect_hybrid,
    )

    points = detector(
        features,
        thresholds,
    )

    events = group_actionable_events(
        points,
        thresholds,
    )

    # =========================================================
    # CHECK-IN DETECTION
    # =========================================================

    checkin_findings = detect_checkins(
        checkin_rows,
        checkpoints=checkpoints,
        thresholds=thresholds,
    )

    # =========================================================
    # PATROL DETECTION
    # =========================================================

    patrol_findings = detect_patrols(
        patrol_rows,
        thresholds=thresholds,
    )

    # =========================================================
    # CREATE CHECK-IN EVENTS
    # =========================================================

    checkin_events = _finding_events(
        checkin_findings,
        checkin_rows,
        len(events),
    )

    # =========================================================
    # CREATE PATROL EVENTS
    # =========================================================

    patrol_events = _finding_events(
        patrol_findings,
        patrol_rows,
        len(events) + len(checkin_events),
    )

    all_events = [
        *events,
        *checkin_events,
        *patrol_events,
    ]

    # =========================================================
    # PERSIST RESULTS
    # =========================================================

    if persist:

        persist_detection(
            session,
            points,
            all_events,
        )

        _mark_processed(
            session,
            incremental,
        )

    # =========================================================
    # ALERTS
    # =========================================================

    alert_results: list[dict[str, Any]] = []

    if send_alerts:

        alert_results = send_alerts_for_events(
            session,
            all_events,
            thresholds,
        )

    return {
        "method": method,
        "incremental": incremental,
        "gps_points": len(features),
        "anomalies": sum(
            1
            for point in points
            if point.is_anomaly
        ),
        "actionable_events": len(all_events),
        "checkin_findings": checkin_findings,
        "patrol_findings": patrol_findings,
        "alerts": alert_results,
        "events": all_events,
    }


def _gps_types_by_guard(
    points: list[Any],
) -> dict[str, set[str]]:

    grouped: dict[str, set[str]] = {}

    for point in points:

        if not point.is_anomaly:
            continue

        grouped.setdefault(
            point.guard_id,
            set(),
        ).add(
            point.anomaly_type
            or "BEHAVIORAL_ANOMALY"
        )

    return grouped


def evaluate_approaches(
    session: Session,
) -> dict[str, Any]:

    thresholds = load_thresholds()
    checkpoints = load_checkpoints()

    gps_rows = [
        _row_from_model(row)
        for row in session.exec(
            select(GpsEvent)
        ).all()
    ]

    features = build_gps_features(
        gps_rows,
        thresholds,
    )

    labels = session.exec(
        select(IncidentLabel)
    ).all()

    # =========================================================
    # RUN ALL DETECTORS
    # =========================================================

    rule_points = detect_rule_based(
        features,
        thresholds,
    )

    if_points = detect_isolation_forest(
        features,
        thresholds,
    )

    hybrid_points = detect_hybrid(
        features,
        thresholds,
    )

    # =========================================================
    # CHECK-IN DETECTION
    # =========================================================

    checkin_rows = [
        _row_from_model(row)
        for row in session.exec(
            select(CheckinEvent)
        ).all()
    ]

    checkin_findings = detect_checkins(
        checkin_rows,
        checkpoints=checkpoints,
        thresholds=thresholds,
    )

    # =========================================================
    # PATROL DETECTION
    # =========================================================

    patrol_rows = [
        _row_from_model(row)
        for row in session.exec(
            select(PatrolStop)
        ).all()
    ]

    patrol_findings = detect_patrols(
        patrol_rows,
        thresholds=thresholds,
    )

    # =========================================================
    # PREPARE EVALUATION DATA
    # =========================================================

    checkin_by_id = {
        str(item.get("checkin_id")): item
        for item in checkin_findings
        if item.get("checkin_id")
    }

    rule_gps = _gps_types_by_guard(
        rule_points
    )

    if_gps = _gps_types_by_guard(
        if_points
    )

    hybrid_gps = _gps_types_by_guard(
        hybrid_points
    )

    patrol_types = {
        str(
            item.get("patrol_id")
            or item.get("guard_id")
        ): item.get("anomaly_type")
        for item in patrol_findings
        if item.get("is_anomaly")
    }

    y_true: list[bool] = []

    preds: dict[str, list[bool]] = {
        "rule": [],
        "isolation_forest": [],
        "hybrid": [],
    }

    def _gps_hit(
        store: dict[str, set[str]],
        guard_id: str,
        anomaly_type: str,
    ) -> bool:

        types = store.get(
            guard_id,
            set(),
        )

        return (
            anomaly_type in types
            or bool(types)
        )

    # =========================================================
    # COMPARE PREDICTIONS
    # =========================================================

    for label in labels:

        y_true.append(
            bool(label.is_incident)
        )

        checkin = checkin_by_id.get(
            label.event_id
        )

        if checkin is not None:

            flagged = bool(
                checkin.get("is_anomaly")
            )

            preds["rule"].append(
                flagged
            )

            preds["isolation_forest"].append(
                False
            )

            preds["hybrid"].append(
                flagged
            )

            continue

        preds["rule"].append(
            _gps_hit(
                rule_gps,
                label.guard_id,
                label.anomaly_type,
            )
        )

        preds["isolation_forest"].append(
            _gps_hit(
                if_gps,
                label.guard_id,
                label.anomaly_type,
            )
        )

        preds["hybrid"].append(
            _gps_hit(
                hybrid_gps,
                label.guard_id,
                label.anomaly_type,
            )
        )

    # =========================================================
    # EVALUATION
    # =========================================================

    comparison = (
        compare_methods(
            y_true,
            preds,
        )
        if y_true
        else {
            "methods": {},
            "best_method": None,
        }
    )

    return {
        "labeled_examples": len(y_true),
        "comparison": comparison,
        "gps_anomalies": {
            "rule": sum(
                1
                for item in rule_points
                if item.is_anomaly
            ),
            "isolation_forest": sum(
                1
                for item in if_points
                if item.is_anomaly
            ),
            "hybrid": sum(
                1
                for item in hybrid_points
                if item.is_anomaly
            ),
        },
        "checkin_anomalies": sum(
            1
            for item in checkin_findings
            if item["is_anomaly"]
        ),
        "patrol_anomalies": sum(
            1
            for item in patrol_findings
            if item["is_anomaly"]
        ),
        "patrol_types": patrol_types,
    }