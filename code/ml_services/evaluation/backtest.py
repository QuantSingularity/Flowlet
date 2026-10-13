from typing import Any, Callable, Dict, List

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from .metrics import classification_metrics


def walk_forward_validation(
    features: pd.DataFrame,
    labels: Any,
    model_factory: Callable[[], Any],
    n_splits: int = 4,
    threshold: float = 0.5,
) -> Dict[str, Any]:
    y = np.asarray(labels).astype(int)
    folds: List[Dict[str, Any]] = []
    splitter = TimeSeriesSplit(n_splits=n_splits)
    for index, (train_idx, test_idx) in enumerate(splitter.split(features)):
        if len(np.unique(y[train_idx])) < 2 or len(np.unique(y[test_idx])) < 2:
            continue
        model = model_factory()
        model.train(features.iloc[train_idx], y[train_idx])
        scores = model.predict(features.iloc[test_idx])
        metrics = classification_metrics(y[test_idx], scores, threshold)
        metrics["fold"] = index
        metrics["train_size"] = int(len(train_idx))
        folds.append(metrics)
    summary: Dict[str, Any] = {"folds": folds}
    for key in ("roc_auc", "average_precision", "precision", "recall", "f1"):
        values = [fold[key] for fold in folds if fold.get(key) is not None]
        summary[f"mean_{key}"] = float(np.mean(values)) if values else None
        summary[f"std_{key}"] = float(np.std(values)) if values else None
    return summary
