import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd

from ...core.enums import RiskLevel
from ...core.exceptions import FraudDetectionError, ModelNotTrainedError
from ...core.logging import get_logger


def _to_frame(data: Any) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, pd.Series):
        return data.to_frame().T
    if isinstance(data, dict):
        return pd.DataFrame([data])
    array = np.asarray(data)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    return pd.DataFrame(array)


class FraudModelBase(ABC):
    def __init__(self, model_config: Optional[Dict[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = dict(model_config or {})
        self.model: Any = None
        self.is_trained = False
        self.feature_columns: List[str] = []
        self.model_version = str(uuid.uuid4())
        self.training_timestamp: Optional[str] = None
        self.feature_stats: Dict[str, Dict[str, float]] = {}
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def train(self, training_data: Any, labels: Any = None) -> None: ...

    @abstractmethod
    def predict(self, features: Any) -> np.ndarray: ...

    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]: ...

    def _begin_training(self, training_data: Any) -> pd.DataFrame:
        frame = _to_frame(training_data)
        if frame.empty:
            raise FraudDetectionError("Training data is empty")
        if not self.feature_columns or not self.is_trained:
            self.feature_columns = [str(column) for column in frame.columns]
        frame = frame.copy()
        frame.columns = [str(column) for column in frame.columns]
        frame = self._clean(frame)
        self.feature_stats = {
            column: {
                "mean": float(frame[column].mean()),
                "std": float(frame[column].std(ddof=0)) or 1.0,
            }
            for column in self.feature_columns
        }
        return frame

    def _finish_training(self) -> None:
        self.is_trained = True
        self.model_version = str(uuid.uuid4())
        self.training_timestamp = datetime.now(timezone.utc).isoformat()

    def _clean(self, frame: pd.DataFrame) -> pd.DataFrame:
        for column in self.feature_columns:
            if column not in frame.columns:
                frame[column] = 0.0
        frame = frame[self.feature_columns]
        frame = frame.apply(pd.to_numeric, errors="coerce")
        frame = frame.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return frame.astype(float)

    def preprocess_features(self, features: Any) -> pd.DataFrame:
        frame = _to_frame(features).copy()
        frame.columns = [str(column) for column in frame.columns]
        if not self.feature_columns:
            self.feature_columns = list(frame.columns)
        return self._clean(frame)

    def _require_trained(self) -> None:
        if not self.is_trained or self.model is None:
            raise ModelNotTrainedError(f"{self.__class__.__name__} is not trained")

    @staticmethod
    def _binary_labels(labels: Any, length: int) -> np.ndarray:
        if labels is None:
            raise FraudDetectionError("Supervised models require labels")
        array = np.asarray(labels).astype(int).ravel()
        if len(array) != length:
            raise FraudDetectionError("Labels and features must have equal length")
        if len(np.unique(array)) < 2:
            raise FraudDetectionError(
                "Labels must contain both fraud and legitimate samples"
            )
        return array

    def calculate_risk_level(self, score: float) -> RiskLevel:
        return RiskLevel.from_score(float(score))

    def local_contributions(self, features: Any) -> Dict[str, float]:
        frame = self.preprocess_features(features)
        if frame.empty:
            return {}
        importance = self.get_feature_importance()
        row = frame.iloc[0]
        contributions: Dict[str, float] = {}
        for column in self.feature_columns:
            stats = self.feature_stats.get(column)
            weight = importance.get(column, 0.0)
            if not stats or not weight:
                continue
            deviation = (float(row[column]) - stats["mean"]) / stats["std"]
            contributions[column] = float(weight * np.clip(deviation, -10.0, 10.0))
        return contributions

    def save_model(self, filepath: str) -> None:
        joblib.dump(self, filepath, compress=3)

    def load_model(self, filepath: str) -> None:
        loaded = joblib.load(filepath)
        if not isinstance(loaded, FraudModelBase):
            raise FraudDetectionError("Artifact is not a fraud model")
        self.__dict__.update(loaded.__dict__)

    def status(self) -> Dict[str, Any]:
        return {
            "trained": self.is_trained,
            "version": self.model_version,
            "training_timestamp": self.training_timestamp,
            "feature_count": len(self.feature_columns),
        }


class QuantileCalibrator:
    def __init__(self) -> None:
        self.reference = np.array([0.0, 1.0])

    def fit(self, raw_scores: np.ndarray) -> "QuantileCalibrator":
        values = np.sort(np.asarray(raw_scores, dtype=float).ravel())
        if len(values) == 0:
            values = np.array([0.0, 1.0])
        if len(values) > 5000:
            positions = np.linspace(0, len(values) - 1, 5000).astype(int)
            values = values[positions]
        self.reference = values
        return self

    def transform(self, raw_scores: np.ndarray) -> np.ndarray:
        values = np.asarray(raw_scores, dtype=float).ravel()
        ranks = np.searchsorted(self.reference, values, side="right")
        return np.clip(ranks / max(len(self.reference), 1), 0.0, 1.0)
