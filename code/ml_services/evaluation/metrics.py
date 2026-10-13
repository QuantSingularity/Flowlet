from typing import Any, Dict, Tuple

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)


def find_best_threshold(y_true: Any, scores: Any) -> Tuple[float, float]:
    y = np.asarray(y_true).astype(int)
    s = np.asarray(scores, dtype=float)
    precision, recall, thresholds = precision_recall_curve(y, s)
    f1 = (
        2
        * precision[:-1]
        * recall[:-1]
        / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    )
    if len(f1) == 0:
        return 0.5, 0.0
    best = int(np.argmax(f1))
    return float(thresholds[best]), float(f1[best])


def classification_metrics(
    y_true: Any, scores: Any, threshold: float = 0.5
) -> Dict[str, Any]:
    y = np.asarray(y_true).astype(int).ravel()
    s = np.clip(np.asarray(scores, dtype=float).ravel(), 0.0, 1.0)
    predicted = (s >= threshold).astype(int)
    tp = int(((predicted == 1) & (y == 1)).sum())
    fp = int(((predicted == 1) & (y == 0)).sum())
    fn = int(((predicted == 0) & (y == 1)).sum())
    tn = int(((predicted == 0) & (y == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    result: Dict[str, Any] = {
        "samples": int(len(y)),
        "fraud_rate": float(y.mean()) if len(y) else 0.0,
        "threshold": float(threshold),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": (tp + tn) / len(y) if len(y) else 0.0,
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }
    if len(np.unique(y)) == 2:
        fpr, tpr, _ = roc_curve(y, s)
        result["roc_auc"] = float(roc_auc_score(y, s))
        result["average_precision"] = float(average_precision_score(y, s))
        result["ks_statistic"] = float(np.max(tpr - fpr))
        result["brier_score"] = float(brier_score_loss(y, s))
        within = fpr <= 0.01
        result["recall_at_1pct_fpr"] = float(tpr[within].max()) if within.any() else 0.0
        best_threshold, best_f1 = find_best_threshold(y, s)
        result["best_f1_threshold"] = best_threshold
        result["best_f1"] = best_f1
    else:
        result["roc_auc"] = None
        result["average_precision"] = None
    return result
