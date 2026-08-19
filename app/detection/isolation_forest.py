from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

from app.config import load_thresholds
from app.detection.types import GpsFeature


FEATURE_COLUMNS = (
    "time_gap_seconds",
    "distance_from_previous_m",
    "speed_kmh",
    "distance_to_road_m",
)


def _minmax(values: np.ndarray) -> np.ndarray:
    vmin = float(values.min())
    vmax = float(values.max())
    if vmax - vmin < 1e-9:
        return np.zeros_like(values)
    return (values - vmin) / (vmax - vmin)


def detect_isolation_forest(
    points: list[GpsFeature],
    thresholds: dict[str, Any] | None = None,
) -> list[GpsFeature]:
    cfg = thresholds or load_thresholds()
    if_cfg = cfg["isolation_forest"]
    hybrid_cfg = cfg["hybrid"]
    risk_cfg = cfg["risk"]
    cutoff = float(hybrid_cfg["anomaly_score_threshold"])

    if len(points) < 2:
        result = []
        for point in points:
            updated = point.model_copy(deep=True)
            updated.detection_method = "isolation_forest"
            result.append(updated)
        return result

    matrix = np.array(
        [
            [
                point.time_gap_seconds,
                point.distance_from_previous_m,
                point.speed_kmh,
                point.distance_to_road_m,
            ]
            for point in points
        ],
        dtype=float,
    )
    matrix = np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)

    contamination: Any = if_cfg.get("contamination", "auto")
    if contamination != "auto":
        contamination = float(contamination)

    model = IsolationForest(
        n_estimators=int(if_cfg.get("n_estimators", 200)),
        contamination=contamination,
        random_state=int(if_cfg.get("random_state", 42)),
        n_jobs=-1,
    )
    predictions = model.fit_predict(matrix)
    raw_scores = -model.decision_function(matrix)
    normalized = _minmax(raw_scores)

    scored: list[GpsFeature] = []
    for point, pred, ml_score in zip(points, predictions, normalized):
        updated = point.model_copy(deep=True)
        updated.ml_score = float(ml_score)
        updated.hybrid_score = float(ml_score)
        updated.rule_score = 0.0
        updated.is_anomaly = bool(pred == -1) or float(ml_score) >= cutoff
        updated.risk_level = (
            "Critical"
            if ml_score >= float(risk_cfg["critical"])
            else "High"
            if ml_score >= float(risk_cfg["high"])
            else "Medium"
            if ml_score >= float(risk_cfg["medium"])
            else "Low"
        )
        updated.detection_method = "isolation_forest"
        if updated.is_anomaly:
            updated.reasons = ["Isolation Forest detected abnormal behavior"]
            updated.anomaly_type = updated.anomaly_type or "BEHAVIORAL_ANOMALY"
        scored.append(updated)
    return scored
