from __future__ import annotations

from typing import Any


def confusion_counts(
    y_true: list[bool],
    y_pred: list[bool],
) -> dict[str, int]:
    tp = fp = tn = fn = 0
    for truth, pred in zip(y_true, y_pred):
        if truth and pred:
            tp += 1
        elif not truth and pred:
            fp += 1
        elif not truth and not pred:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def classification_metrics(
    y_true: list[bool],
    y_pred: list[bool],
) -> dict[str, float | int]:
    counts = confusion_counts(y_true, y_pred)
    tp, fp, tn, fn = counts["tp"], counts["fp"], counts["tn"], counts["fn"]
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        (2 * precision * recall / (precision + recall))
        if (precision + recall)
        else 0.0
    )
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    return {
        **counts,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "support": len(y_true),
    }


def compare_methods(
    y_true: list[bool],
    predictions: dict[str, list[bool]],
) -> dict[str, Any]:
    results = {
        name: classification_metrics(y_true, preds)
        for name, preds in predictions.items()
    }
    ranked = sorted(
        results.items(),
        key=lambda item: (
            float(item[1]["f1"]),
            float(item[1]["precision"]),
        ),
        reverse=True,
    )
    return {
        "methods": results,
        "best_method": ranked[0][0] if ranked else None,
    }
