import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ..config import MLSettings, get_settings
from ..core.exceptions import FraudDetectionError
from ..core.logging import get_logger
from ..data.validation import normalize_transaction
from ..evaluation.metrics import classification_metrics
from ..features.engineering import FeatureEngineer
from ..features.history import InMemoryHistoryStore
from ..features.schema import FEATURE_COLUMNS
from ..fraud_detection.models.ensemble import EnsembleFraudModel, default_model_config

logger = get_logger(__name__)

MIN_HOLDOUT_SAMPLES = 200


@dataclass
class TrainingResult:
    model: EnsembleFraudModel
    metrics: Dict[str, Any] = field(default_factory=dict)
    training_samples: int = 0
    holdout_samples: int = 0
    duration_seconds: float = 0.0
    holdout: Optional[Tuple[pd.DataFrame, np.ndarray]] = None


def build_training_frame(
    transactions: List[Dict[str, Any]],
    label_key: str = "is_fraud",
    settings: Optional[MLSettings] = None,
) -> Tuple[pd.DataFrame, pd.Series]:
    settings = settings or get_settings()
    engineer = FeatureEngineer(settings)
    store = InMemoryHistoryStore(
        settings.max_history_per_user, 3650, max_users=1_000_000
    )
    normalized = []
    for item in transactions:
        if label_key not in item:
            raise FraudDetectionError(f"Transaction is missing label field {label_key}")
        tx = normalize_transaction(item)
        tx["_normalized"] = True
        normalized.append((tx, int(bool(item[label_key]))))
    normalized.sort(key=lambda pair: pair[0]["timestamp"])
    rows = []
    labels = []
    for tx, label in normalized:
        history = store.get(tx["user_id"])
        features = engineer.extract_transaction_features(tx, history)
        rows.append(engineer.features_to_row(features))
        labels.append(label)
        store.append(tx["user_id"], tx)
    frame = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    return frame, pd.Series(labels, name=label_key)


def _frame(data: Any) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data
    return pd.DataFrame(data)


def train_ensemble(
    training_data: Any,
    labels: Any = None,
    validation: Optional[Tuple[Any, Any]] = None,
    model_config: Optional[Dict[str, Any]] = None,
    settings: Optional[MLSettings] = None,
    training_source: str = "supplied",
) -> TrainingResult:
    settings = settings or get_settings()
    started = time.perf_counter()
    frame = _frame(training_data).reset_index(drop=True)
    target = None if labels is None else np.asarray(labels).astype(int).ravel()
    if target is not None and len(target) != len(frame):
        raise FraudDetectionError("Labels and training data must have equal length")
    config = model_config if model_config is not None else default_model_config()
    config = dict(config)
    config.setdefault("random_state", settings.random_state)
    holdout: Optional[Tuple[pd.DataFrame, np.ndarray]] = None
    train_frame, train_target = frame, target
    if validation is not None and validation[0] is not None and len(validation[0]) > 0:
        validation_frame = _frame(validation[0]).reset_index(drop=True)
        validation_target = np.asarray(validation[1]).astype(int).ravel()
        if len(validation_target) == len(validation_frame):
            holdout = (validation_frame, validation_target)
    elif (
        target is not None
        and len(frame) >= MIN_HOLDOUT_SAMPLES
        and len(np.unique(target)) == 2
        and min(np.bincount(target)) >= 10
    ):
        train_frame, holdout_frame, train_target, holdout_target = train_test_split(
            frame,
            target,
            test_size=0.2,
            stratify=target,
            random_state=settings.random_state,
        )
        train_frame = train_frame.reset_index(drop=True)
        holdout = (holdout_frame.reset_index(drop=True), np.asarray(holdout_target))
    model = EnsembleFraudModel(config)
    model.training_source = training_source
    model.train(train_frame, train_target)
    metrics: Dict[str, Any] = {}
    if holdout is not None:
        scores = model.predict(holdout[0])
        metrics = classification_metrics(holdout[1], scores, settings.high_threshold)
    return TrainingResult(
        model=model,
        metrics=metrics,
        training_samples=len(train_frame),
        holdout_samples=0 if holdout is None else len(holdout[0]),
        duration_seconds=time.perf_counter() - started,
        holdout=holdout,
    )
