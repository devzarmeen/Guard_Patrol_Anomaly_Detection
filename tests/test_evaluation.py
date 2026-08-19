from app.evaluation.metrics import classification_metrics, compare_methods


def test_precision_recall_f1_and_fpr():
    y_true = [True, True, False, False, False]
    y_pred = [True, False, True, False, False]
    metrics = classification_metrics(y_true, y_pred)
    assert metrics["tp"] == 1
    assert metrics["fp"] == 1
    assert metrics["fn"] == 1
    assert metrics["tn"] == 2
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5
    assert metrics["false_positive_rate"] == 0.3333


def test_compare_methods_selects_best_f1():
    y_true = [True, True, False, False]
    result = compare_methods(
        y_true,
        {
            "rule": [True, True, True, False],
            "isolation_forest": [True, False, False, False],
            "hybrid": [True, True, False, False],
        },
    )
    assert result["best_method"] == "hybrid"
    assert result["methods"]["hybrid"]["f1"] == 1.0
