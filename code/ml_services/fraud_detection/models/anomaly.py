import warnings
from typing import Any, Dict

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from ...core.exceptions import FraudDetectionError
from .base import FraudModelBase, QuantileCalibrator


class _AnomalyModel(FraudModelBase):
    scaler: StandardScaler
    calibrator: QuantileCalibrator

    def _fit_frame(self, training_data: Any, labels: Any) -> np.ndarray:
        frame = self._begin_training(training_data)
        matrix = frame.to_numpy()
        if labels is not None:
            array = np.asarray(labels).astype(int).ravel()
            if len(array) == len(matrix) and (array == 0).sum() >= 10:
                matrix = matrix[array == 0]
        if len(matrix) < 10:
            raise FraudDetectionError("At least 10 samples are required")
        self.scaler = StandardScaler().fit(matrix)
        return self.scaler.transform(matrix)

    def _scaled(self, features: Any) -> np.ndarray:
        self._require_trained()
        frame = self.preprocess_features(features)
        return np.clip(self.scaler.transform(frame.to_numpy()), -20.0, 20.0)

    def _raw(self, scaled: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def predict(self, features: Any) -> np.ndarray:
        scaled = self._scaled(features)
        return self.calibrator.transform(self._raw(scaled))

    def get_feature_importance(self) -> Dict[str, float]:
        if not self.feature_columns:
            return {}
        return {
            column: 1.0 / len(self.feature_columns) for column in self.feature_columns
        }


class IsolationForestModel(_AnomalyModel):
    def train(self, training_data: Any, labels: Any = None) -> None:
        scaled = self._fit_frame(training_data, labels)
        self.model = IsolationForest(
            n_estimators=int(self.config.get("n_estimators", 100)),
            contamination=self.config.get("contamination", "auto"),
            max_samples=self.config.get("max_samples", "auto"),
            random_state=int(self.config.get("random_state", 42)),
            n_jobs=int(self.config.get("n_jobs", 1)),
        )
        self.model.fit(scaled)
        self.calibrator = QuantileCalibrator().fit(self._raw(scaled))
        self._finish_training()

    def _raw(self, scaled: np.ndarray) -> np.ndarray:
        return -self.model.score_samples(scaled)


class OneClassSVMModel(_AnomalyModel):
    def train(self, training_data: Any, labels: Any = None) -> None:
        scaled = self._fit_frame(training_data, labels)
        limit = int(self.config.get("max_training_samples", 2000))
        if len(scaled) > limit:
            rng = np.random.default_rng(int(self.config.get("random_state", 42)))
            scaled = scaled[rng.choice(len(scaled), limit, replace=False)]
        self.model = OneClassSVM(
            nu=float(self.config.get("nu", 0.05)),
            kernel=self.config.get("kernel", "rbf"),
            gamma=self.config.get("gamma", "scale"),
        )
        self.model.fit(scaled)
        self.calibrator = QuantileCalibrator().fit(self._raw(scaled))
        self._finish_training()

    def _raw(self, scaled: np.ndarray) -> np.ndarray:
        return -self.model.decision_function(scaled)


class AutoencoderModel(_AnomalyModel):
    def train(self, training_data: Any, labels: Any = None) -> None:
        scaled = self._fit_frame(training_data, labels)
        width = len(self.feature_columns)
        hidden = int(self.config.get("hidden_units", max(8, width // 2)))
        bottleneck = int(self.config.get("bottleneck_units", max(3, width // 4)))
        self.model = MLPRegressor(
            hidden_layer_sizes=(hidden, bottleneck, hidden),
            activation="relu",
            solver="adam",
            max_iter=int(self.config.get("max_iter", 120)),
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=8,
            random_state=int(self.config.get("random_state", 42)),
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            self.model.fit(scaled, scaled)
        self.calibrator = QuantileCalibrator().fit(self._raw(scaled))
        self._finish_training()

    def _raw(self, scaled: np.ndarray) -> np.ndarray:
        reconstruction = self.model.predict(scaled)
        return np.mean((scaled - reconstruction) ** 2, axis=1)
