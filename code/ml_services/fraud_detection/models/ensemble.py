import copy
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from ...core.exceptions import (
    DependencyUnavailableError,
    FraudDetectionError,
    ModelNotTrainedError,
)
from .anomaly import AutoencoderModel, IsolationForestModel, OneClassSVMModel
from .base import FraudModelBase
from .supervised import (
    LightGBMFraudModel,
    NeuralNetworkFraudModel,
    RandomForestFraudModel,
    XGBoostFraudModel,
)

ANOMALY_REGISTRY = {
    "isolation_forest": IsolationForestModel,
    "one_class_svm": OneClassSVMModel,
    "autoencoder": AutoencoderModel,
}

SUPERVISED_MODELS = {
    "random_forest": RandomForestFraudModel,
    "xgboost": XGBoostFraudModel,
    "lightgbm": LightGBMFraudModel,
    "neural_network": NeuralNetworkFraudModel,
}

MODEL_REGISTRY = {**ANOMALY_REGISTRY, **SUPERVISED_MODELS}

DEFAULT_MODEL_CONFIG: Dict[str, Any] = {
    "voting_strategy": "stacking",
    "anomaly_weight": 0.3,
    "supervised_weight": 0.7,
    "cv_folds": 3,
    "random_state": 42,
    "models": {
        "isolation_forest": {"n_estimators": 100},
        "one_class_svm": {"max_training_samples": 1500, "nu": 0.05},
        "autoencoder": {"max_iter": 80},
        "random_forest": {"n_estimators": 100, "max_depth": 12},
        "xgboost": {"n_estimators": 100, "max_depth": 5},
        "lightgbm": {"n_estimators": 100},
        "neural_network": {"max_iter": 80},
    },
}


def default_model_config() -> Dict[str, Any]:
    return copy.deepcopy(DEFAULT_MODEL_CONFIG)


def _weighted_voting(
    scores: Dict[str, np.ndarray], anomaly_weight: float, supervised_weight: float
) -> np.ndarray:
    anomaly = [v for k, v in scores.items() if k in ANOMALY_REGISTRY]
    supervised = [v for k, v in scores.items() if k in SUPERVISED_MODELS]
    other = [v for k, v in scores.items() if k not in MODEL_REGISTRY]
    parts: List[Tuple[float, np.ndarray]] = []
    if anomaly:
        parts.append((anomaly_weight, np.mean(anomaly, axis=0)))
    if supervised:
        parts.append((supervised_weight, np.mean(supervised, axis=0)))
    if other:
        parts.append((0.5, np.mean(other, axis=0)))
    if not parts:
        raise FraudDetectionError("No member scores available")
    total = sum(weight for weight, _ in parts) or 1.0
    return np.clip(sum(weight * value for weight, value in parts) / total, 0.0, 1.0)


def _average_voting(scores: Dict[str, np.ndarray]) -> np.ndarray:
    if not scores:
        raise FraudDetectionError("No member scores available")
    return np.clip(np.mean(list(scores.values()), axis=0), 0.0, 1.0)


class EnsembleFraudModel(FraudModelBase):
    def __init__(self, model_config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(model_config)
        self.models: Dict[str, FraudModelBase] = {}
        self.skipped: Dict[str, str] = {}
        self.voting_strategy = self.config.get("voting_strategy", "weighted")
        self.anomaly_weight = float(self.config.get("anomaly_weight", 0.3))
        self.supervised_weight = float(self.config.get("supervised_weight", 0.7))
        self.meta_model: Optional[LogisticRegression] = None
        self.meta_order: List[str] = []
        self.training_source = "unknown"
        self.last_member_scores: Dict[str, float] = {}

    def _configured_models(self) -> Dict[str, Dict[str, Any]]:
        configured = self.config.get("models")
        if configured is None:
            configured = default_model_config()["models"]
        seed = int(self.config.get("random_state", 42))
        prepared = {}
        for name, params in configured.items():
            merged = dict(params or {})
            merged.setdefault("random_state", seed)
            prepared[name] = merged
        return prepared

    @staticmethod
    def _labels_usable(labels: Any, length: int) -> Optional[np.ndarray]:
        if labels is None:
            return None
        array = np.asarray(labels).astype(int).ravel()
        if len(array) != length or len(np.unique(array)) < 2:
            return None
        return array

    def train(self, training_data: Any, labels: Any = None) -> None:
        frame = self._begin_training(training_data)
        target = self._labels_usable(labels, len(frame))
        trained: Dict[str, FraudModelBase] = {}
        skipped: Dict[str, str] = {}
        for name, params in self._configured_models().items():
            cls = MODEL_REGISTRY.get(name)
            if cls is None:
                skipped[name] = "unknown model"
                continue
            if name in SUPERVISED_MODELS and target is None:
                skipped[name] = "labels with both classes are required"
                continue
            member = cls(params)
            member.feature_columns = list(self.feature_columns)
            try:
                member.train(frame, target)
            except DependencyUnavailableError as exc:
                skipped[name] = str(exc)
                continue
            except Exception as exc:
                self.logger.error("Training %s failed: %s", name, exc)
                skipped[name] = f"training failed: {exc}"
                continue
            trained[name] = member
        if not trained:
            raise FraudDetectionError(f"No ensemble member could be trained: {skipped}")
        self.models = trained
        self.skipped = skipped
        self.meta_model = None
        self.meta_order = []
        if self.voting_strategy == "stacking":
            has_supervised = any(name in SUPERVISED_MODELS for name in trained)
            if has_supervised and target is not None:
                self._fit_meta_model(frame, target)
            else:
                self.voting_strategy = "weighted"
        self._finish_training()

    def _fit_meta_model(self, frame: pd.DataFrame, target: np.ndarray) -> None:
        folds = int(self.config.get("cv_folds", 3))
        minority = int(min(target.sum(), len(target) - target.sum()))
        if minority < folds * 2:
            self.logger.warning("Too few minority samples for stacking, using weighted")
            self.voting_strategy = "weighted"
            return
        names = list(self.models.keys())
        oof = np.zeros((len(frame), len(names)))
        splitter = StratifiedKFold(
            n_splits=folds,
            shuffle=True,
            random_state=int(self.config.get("random_state", 42)),
        )
        params = self._configured_models()
        usable = np.ones(len(names), dtype=bool)
        for train_index, valid_index in splitter.split(frame, target):
            train_frame = frame.iloc[train_index]
            valid_frame = frame.iloc[valid_index]
            for column, name in enumerate(names):
                if not usable[column]:
                    continue
                member = MODEL_REGISTRY[name](params[name])
                member.feature_columns = list(self.feature_columns)
                try:
                    member.train(train_frame, target[train_index])
                    oof[valid_index, column] = member.predict(valid_frame)
                except Exception as exc:
                    self.logger.warning("OOF fold for %s failed: %s", name, exc)
                    usable[column] = False
        if not usable.any():
            self.voting_strategy = "weighted"
            return
        kept = [name for name, flag in zip(names, usable) if flag]
        matrix = oof[:, usable]
        meta = LogisticRegression(
            C=1.0, class_weight="balanced", max_iter=1000, solver="lbfgs"
        )
        meta.fit(matrix, target)
        self.meta_model = meta
        self.meta_order = kept

    def predict_members(self, features: Any) -> Dict[str, np.ndarray]:
        if not self.is_trained or not self.models:
            raise ModelNotTrainedError("Ensemble model not trained")
        frame = self.preprocess_features(features)
        scores: Dict[str, np.ndarray] = {}
        for name, member in self.models.items():
            try:
                scores[name] = np.asarray(member.predict(frame), dtype=float)
            except Exception as exc:
                self.logger.error("Member %s failed during prediction: %s", name, exc)
        if not scores:
            raise FraudDetectionError("All ensemble members failed during prediction")
        return scores

    def combine(self, scores: Dict[str, np.ndarray]) -> np.ndarray:
        strategy = self.voting_strategy
        if strategy == "stacking" and self.meta_model is not None:
            if all(name in scores for name in self.meta_order):
                matrix = np.column_stack([scores[name] for name in self.meta_order])
                return np.clip(self.meta_model.predict_proba(matrix)[:, 1], 0.0, 1.0)
            return _weighted_voting(scores, self.anomaly_weight, self.supervised_weight)
        if strategy == "average":
            return _average_voting(scores)
        return _weighted_voting(scores, self.anomaly_weight, self.supervised_weight)

    def predict(self, features: Any) -> np.ndarray:
        scores = self.predict_members(features)
        combined = self.combine(scores)
        self.last_member_scores = {
            name: float(value[0]) for name, value in scores.items()
        }
        return combined

    def predict_with_details(
        self, features: Any
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        scores = self.predict_members(features)
        return self.combine(scores), scores

    def _weighted_voting(self, features: Any) -> np.ndarray:
        return _weighted_voting(
            self.predict_members(features), self.anomaly_weight, self.supervised_weight
        )

    def _average_voting(self, features: Any) -> np.ndarray:
        return _average_voting(self.predict_members(features))

    def get_feature_importance(self) -> Dict[str, float]:
        supervised = [
            member
            for name, member in self.models.items()
            if name in SUPERVISED_MODELS and member.is_trained
        ]
        sources = supervised or list(self.models.values())
        combined: Dict[str, float] = {}
        for member in sources:
            for feature, value in member.get_feature_importance().items():
                combined[feature] = combined.get(feature, 0.0) + float(value)
        count = len(sources) or 1
        return {feature: value / count for feature, value in combined.items()}

    def local_contributions(self, features: Any) -> Dict[str, float]:
        for name in ("xgboost", "lightgbm", "random_forest", "neural_network"):
            member = self.models.get(name)
            if member is not None and member.is_trained:
                try:
                    return member.local_contributions(features)
                except Exception as exc:
                    self.logger.warning("Contribution from %s failed: %s", name, exc)
        return super().local_contributions(features)

    def get_model_status(self) -> Dict[str, Any]:
        status: Dict[str, Any] = {
            name: {
                "trained": member.is_trained,
                "version": member.model_version,
                "training_timestamp": member.training_timestamp,
            }
            for name, member in self.models.items()
        }
        return status

    def status(self) -> Dict[str, Any]:
        base = super().status()
        base.update(
            {
                "voting_strategy": self.voting_strategy,
                "members": self.get_model_status(),
                "skipped_members": dict(self.skipped),
                "training_source": self.training_source,
                "stacking_active": self.meta_model is not None,
            }
        )
        return base
