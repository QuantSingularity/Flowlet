import warnings
from typing import Any, Dict, Optional

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from ...core.exceptions import DependencyUnavailableError
from .base import FraudModelBase

try:
    import xgboost as xgb

    XGBOOST_AVAILABLE = True
except Exception:
    xgb = None
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
except Exception:
    lgb = None
    LIGHTGBM_AVAILABLE = False


class _SupervisedModel(FraudModelBase):
    def _prepare(self, training_data: Any, labels: Any):
        frame = self._begin_training(training_data)
        target = self._binary_labels(labels, len(frame))
        return frame, target

    def predict(self, features: Any) -> np.ndarray:
        self._require_trained()
        frame = self.preprocess_features(features)
        probabilities = self.model.predict_proba(self._transform(frame))
        return np.asarray(probabilities)[:, 1]

    def _transform(self, frame):
        return frame

    def _importance_vector(self) -> Optional[np.ndarray]:
        values = getattr(self.model, "feature_importances_", None)
        if values is None:
            return None
        return np.asarray(values, dtype=float)

    def get_feature_importance(self) -> Dict[str, float]:
        if not self.is_trained or not self.feature_columns:
            return {}
        values = self._importance_vector()
        if values is None or len(values) != len(self.feature_columns):
            return {}
        total = float(values.sum()) or 1.0
        return {
            column: float(value / total)
            for column, value in zip(self.feature_columns, values)
        }


class RandomForestFraudModel(_SupervisedModel):
    def train(self, training_data: Any, labels: Any = None) -> None:
        frame, target = self._prepare(training_data, labels)
        self.model = RandomForestClassifier(
            n_estimators=int(self.config.get("n_estimators", 150)),
            max_depth=self.config.get("max_depth", 12),
            min_samples_leaf=int(self.config.get("min_samples_leaf", 2)),
            class_weight=self.config.get("class_weight", "balanced_subsample"),
            n_jobs=int(self.config.get("n_jobs", 1)),
            random_state=int(self.config.get("random_state", 42)),
        )
        self.model.fit(frame, target)
        self._finish_training()


class XGBoostFraudModel(_SupervisedModel):
    def train(self, training_data: Any, labels: Any = None) -> None:
        if not XGBOOST_AVAILABLE:
            raise DependencyUnavailableError("xgboost is not installed")
        frame, target = self._prepare(training_data, labels)
        positives = max(int(target.sum()), 1)
        negatives = max(int(len(target) - target.sum()), 1)
        self.model = xgb.XGBClassifier(
            n_estimators=int(self.config.get("n_estimators", 150)),
            max_depth=int(self.config.get("max_depth", 5)),
            learning_rate=float(self.config.get("learning_rate", 0.1)),
            subsample=float(self.config.get("subsample", 0.9)),
            colsample_bytree=float(self.config.get("colsample_bytree", 0.9)),
            scale_pos_weight=float(
                self.config.get("scale_pos_weight", negatives / positives)
            ),
            eval_metric="logloss",
            tree_method="hist",
            n_jobs=int(self.config.get("n_jobs", 1)),
            random_state=int(self.config.get("random_state", 42)),
        )
        self.model.fit(frame, target)
        self._finish_training()

    def local_contributions(self, features: Any) -> Dict[str, float]:
        self._require_trained()
        frame = self.preprocess_features(features)
        try:
            booster = self.model.get_booster()
            matrix = xgb.DMatrix(frame, feature_names=list(frame.columns))
            contribs = booster.predict(matrix, pred_contribs=True)[0][:-1]
            return {c: float(v) for c, v in zip(frame.columns, contribs)}
        except Exception:
            return super().local_contributions(features)


class LightGBMFraudModel(_SupervisedModel):
    def train(self, training_data: Any, labels: Any = None) -> None:
        if not LIGHTGBM_AVAILABLE:
            raise DependencyUnavailableError("lightgbm is not installed")
        frame, target = self._prepare(training_data, labels)
        self.model = lgb.LGBMClassifier(
            n_estimators=int(self.config.get("n_estimators", 150)),
            learning_rate=float(self.config.get("learning_rate", 0.1)),
            num_leaves=int(self.config.get("num_leaves", 31)),
            min_child_samples=int(self.config.get("min_child_samples", 10)),
            class_weight=self.config.get("class_weight", "balanced"),
            n_jobs=int(self.config.get("n_jobs", 1)),
            random_state=int(self.config.get("random_state", 42)),
            verbose=-1,
        )
        self.model.fit(frame, target)
        self._finish_training()

    def local_contributions(self, features: Any) -> Dict[str, float]:
        self._require_trained()
        frame = self.preprocess_features(features)
        try:
            contribs = self.model.predict(frame, pred_contrib=True)[0][:-1]
            return {c: float(v) for c, v in zip(frame.columns, contribs)}
        except Exception:
            return super().local_contributions(features)


class NeuralNetworkFraudModel(_SupervisedModel):
    scaler: StandardScaler

    def train(self, training_data: Any, labels: Any = None) -> None:
        frame, target = self._prepare(training_data, labels)
        matrix = frame.to_numpy()
        rng = np.random.default_rng(int(self.config.get("random_state", 42)))
        positives = np.where(target == 1)[0]
        negatives = np.where(target == 0)[0]
        if 0 < len(positives) < len(negatives):
            extra = rng.choice(positives, len(negatives) - len(positives), replace=True)
            keep = np.concatenate([np.arange(len(target)), extra])
            matrix = matrix[keep]
            target = target[keep]
        self.scaler = StandardScaler().fit(matrix)
        self.model = MLPClassifier(
            hidden_layer_sizes=tuple(self.config.get("hidden_layers", (64, 32))),
            activation="relu",
            solver="adam",
            alpha=float(self.config.get("alpha", 1e-4)),
            max_iter=int(self.config.get("max_iter", 150)),
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=8,
            random_state=int(self.config.get("random_state", 42)),
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            self.model.fit(self.scaler.transform(matrix), target)
        self._finish_training()

    def _transform(self, frame):
        return np.clip(self.scaler.transform(frame.to_numpy()), -20.0, 20.0)

    def _importance_vector(self) -> Optional[np.ndarray]:
        weights = np.abs(self.model.coefs_[0]).sum(axis=1)
        return np.asarray(weights, dtype=float)


SUPERVISED_REGISTRY = {
    "random_forest": RandomForestFraudModel,
    "xgboost": XGBoostFraudModel,
    "lightgbm": LightGBMFraudModel,
    "neural_network": NeuralNetworkFraudModel,
}

__all__ = [
    "LIGHTGBM_AVAILABLE",
    "LightGBMFraudModel",
    "NeuralNetworkFraudModel",
    "RandomForestFraudModel",
    "SUPERVISED_REGISTRY",
    "XGBOOST_AVAILABLE",
    "XGBoostFraudModel",
]
