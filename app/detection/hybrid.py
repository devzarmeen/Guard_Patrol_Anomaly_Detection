from __future__ import annotations

from typing import Any

from app.config import load_thresholds
from app.detection.isolation_forest import detect_isolation_forest
from app.detection.rules import detect_rule_based
from app.detection.types import GpsFeature


def detect_hybrid(
    points: list[GpsFeature],
    thresholds: dict[str, Any] | None = None,
) -> list[GpsFeature]:
    cfg = thresholds or load_thresholds()
    hybrid_cfg = cfg["hybrid"]
    risk_cfg = cfg["risk"]
    rule_weight = float(hybrid_cfg.get("rule_weight", 0.5))
    ml_weight = float(hybrid_cfg.get("ml_weight", 0.5))
    cutoff = float(hybrid_cfg["anomaly_score_threshold"])

    rule_points = detect_rule_based(points, cfg)
    ml_points = detect_isolation_forest(points, cfg)
    ml_by_key = {
        (item.guard_id, item.timestamp): item for item in ml_points
    }

    scored: list[GpsFeature] = []
    for rule_point in rule_points:
        ml_point = ml_by_key[(rule_point.guard_id, rule_point.timestamp)]
        hybrid_score = (
            rule_weight * rule_point.rule_score
            + ml_weight * ml_point.ml_score
        )
        updated = rule_point.model_copy(deep=True)
        updated.ml_score = ml_point.ml_score
        updated.hybrid_score = float(hybrid_score)
        updated.detection_method = "hybrid"
        updated.is_anomaly = hybrid_score >= cutoff or (
            rule_point.is_anomaly and ml_point.is_anomaly
        )
        if ml_point.is_anomaly and "Isolation Forest detected abnormal behavior" not in updated.reasons:
            updated.reasons = [
                *updated.reasons,
                "Isolation Forest detected abnormal behavior",
            ]
            updated.anomaly_type = updated.anomaly_type or "BEHAVIORAL_ANOMALY"

        if hybrid_score >= float(risk_cfg["critical"]):
            updated.risk_level = "Critical"
        elif hybrid_score >= float(risk_cfg["high"]):
            updated.risk_level = "High"
        elif hybrid_score >= float(risk_cfg["medium"]):
            updated.risk_level = "Medium"
        else:
            updated.risk_level = "Low"
        scored.append(updated)
    return scored
