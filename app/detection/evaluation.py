from __future__ import annotations

from typing import Any


def calculate_metrics(
    y_true: list[bool],
    y_pred: list[bool],
) -> dict[str, float]:
    """
    Calculate classification metrics for anomaly detection.
    """

    if not y_true:
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "false_positive_rate": 0.0,
        }

    tp = sum(
        1
        for true, pred in zip(y_true, y_pred)
        if true and pred
    )

    tn = sum(
        1
        for true, pred in zip(y_true, y_pred)
        if not true and not pred
    )

    fp = sum(
        1
        for true, pred in zip(y_true, y_pred)
        if not true and pred
    )

    fn = sum(
        1
        for true, pred in zip(y_true, y_pred)
        if true and not pred
    )

    total = tp + tn + fp + fn

    accuracy = (
        (tp + tn) / total
        if total
        else 0.0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn)
        else 0.0
    )

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "false_positive_rate": round(
            false_positive_rate,
            4,
        ),
    }


def compare_methods(
    y_true: list[bool],
    predictions: dict[str, list[bool]],
) -> dict[str, Any]:
    """
    Compare Rule-based, Isolation Forest and Hybrid detectors.
    """

    results: dict[str, Any] = {}

    for method, y_pred in predictions.items():

        metrics = calculate_metrics(
            y_true,
            y_pred,
        )

        results[method] = metrics

    if not results:
        return {
            "methods": {},
            "best_method": None,
        }

    best_method = max(
        results,
        key=lambda method: (
            results[method]["f1_score"],
            results[method]["recall"],
            -results[method]["false_positive_rate"],
        ),
    )

    return {
        "methods": results,
        "best_method": best_method,
    }