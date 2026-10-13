import asyncio
import threading
import time
from collections import OrderedDict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..config import MLSettings, get_settings
from ..core.enums import FraudAction, RiskLevel
from ..core.exceptions import (
    FraudDetectionError,
    ModelIntegrityError,
    ModelNotFoundError,
)
from ..core.logging import get_logger
from ..core.registry import ModelRegistry
from ..data.synthetic import generate_labeled_features
from ..data.validation import normalize_transaction
from ..evaluation.metrics import classification_metrics
from ..features.engineering import FeatureEngineer
from ..features.history import HistoryStore, build_history_store, normalize_history
from ..monitoring.drift import DriftReport, compute_drift
from ..monitoring.performance import PerformanceTracker
from ..monitoring.prometheus import PrometheusExporter
from ..training.pipeline import TrainingResult, build_training_frame, train_ensemble
from .detector import RealTimeFraudDetector
from .models.ensemble import EnsembleFraudModel, default_model_config
from .rules import combine_scores
from .types import FraudAlert

logger = get_logger(__name__)

MODEL_NAME = "fraud_ensemble"
SNAPSHOT_LIMIT = 20000
RECENT_FEATURES_LIMIT = 5000


class FraudDetectionService:
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        settings: Optional[MLSettings] = None,
        registry: Optional[ModelRegistry] = None,
        history_store: Optional[HistoryStore] = None,
    ) -> None:
        self.config: Dict[str, Any] = dict(config or {})
        self.settings = settings or get_settings()
        self.auto_retrain: bool = bool(
            self.config.get("auto_retrain", self.settings.auto_retrain)
        )
        self.retrain_threshold_days: int = int(
            self.config.get(
                "retrain_threshold_days", self.settings.retrain_interval_days
            )
        )
        self.model_config: Dict[str, Any] = (
            self.config.get("model_config") or default_model_config()
        )
        self.persist: bool = bool(
            self.config.get("persist", self.settings.persist_models)
        )
        self.logger = logger
        self._lock = threading.RLock()
        self._warm_thread: Optional[threading.Thread] = None
        self.registry: Optional[ModelRegistry] = registry
        if self.registry is None and self.persist:
            try:
                self.registry = ModelRegistry(
                    self.settings.model_dir,
                    self.settings.signing_key,
                    self.settings.keep_versions,
                    require_key=self.settings.is_production,
                )
            except Exception as exc:
                logger.warning("Model persistence disabled: %s", exc)
                self.registry = None
        self.history_store: HistoryStore = history_store or build_history_store(
            self.settings
        )
        self.feature_engineer = FeatureEngineer(self.settings)
        self.ensemble_model: EnsembleFraudModel = EnsembleFraudModel(self.model_config)
        self.real_time_detector = RealTimeFraudDetector(
            self.ensemble_model,
            settings=self.settings,
            feature_engineer=self.feature_engineer,
            history_store=self.history_store,
        )
        self.performance_metrics: Dict[str, Any] = {
            "total_predictions": 0,
            "fraud_detected": 0,
            "false_positives": 0,
            "true_positives": 0,
            "false_negatives": 0,
            "true_negatives": 0,
            "last_retrain": None,
        }
        self.alerts_storage: Deque[FraudAlert] = deque(
            maxlen=self.settings.alert_retention
        )
        self._alerts_by_tx: "OrderedDict[str, FraudAlert]" = OrderedDict()
        self._feature_cache: "OrderedDict[str, Dict[str, float]]" = OrderedDict()
        self._feedback: Dict[str, bool] = {}
        self._feedback_rows: List[Dict[str, float]] = []
        self._feedback_labels: List[int] = []
        self._feedback_since_train = 0
        self._snapshot: Optional[Tuple[pd.DataFrame, np.ndarray]] = None
        self._reference_features: Optional[pd.DataFrame] = None
        self._recent_features: Deque[Dict[str, float]] = deque(
            maxlen=RECENT_FEATURES_LIMIT
        )
        self._last_drift: Optional[DriftReport] = None
        self._last_training: Dict[str, Any] = {}
        self.tracker = PerformanceTracker()
        self.exporter = PrometheusExporter()
        self._loaded_registry_version: Optional[str] = None
        self._last_refresh_check = 0.0

    @property
    def model_ready(self) -> bool:
        return self.ensemble_model.is_trained

    def model_version(self) -> Optional[str]:
        return self.ensemble_model.model_version if self.ensemble_model else None

    def _install_model(self, model: EnsembleFraudModel) -> None:
        with self._lock:
            self.ensemble_model = model
            self.real_time_detector.set_model(model)
        self.exporter.set_ready(model.is_trained)

    def warm_up(self, block: bool = True, bootstrap: Optional[bool] = None) -> bool:
        if not block:
            with self._lock:
                if self._warm_thread and self._warm_thread.is_alive():
                    return self.model_ready
                self._warm_thread = threading.Thread(
                    target=self._warm_up_safe,
                    args=(bootstrap,),
                    daemon=True,
                    name="ml-warmup",
                )
                self._warm_thread.start()
            return self.model_ready
        return self._warm_up_safe(bootstrap)

    def _warm_up_safe(self, bootstrap: Optional[bool]) -> bool:
        try:
            if self.load_latest_model():
                return True
            allowed = (
                self.settings.bootstrap_on_start if bootstrap is None else bootstrap
            )
            if allowed:
                self.bootstrap()
            return self.model_ready
        except Exception as exc:
            logger.error("Model warm up failed: %s", exc)
            return False

    def load_latest_model(self) -> bool:
        if self.registry is None:
            return False
        try:
            artifact, manifest = self.registry.load(MODEL_NAME)
        except (ModelNotFoundError, ModelIntegrityError) as exc:
            logger.warning("No usable stored model: %s", exc)
            return False
        except Exception as exc:
            logger.error("Stored model load failed: %s", exc)
            return False
        if not isinstance(artifact, EnsembleFraudModel) or not artifact.is_trained:
            return False
        self._install_model(artifact)
        self._loaded_registry_version = manifest.get("version")
        metadata = manifest.get("metadata", {})
        self._last_training = {
            "version": manifest.get("version"),
            "metrics": metadata.get("metrics", {}),
            "training_source": metadata.get(
                "training_source", artifact.training_source
            ),
            "training_samples": metadata.get("training_samples"),
            "loaded_from_registry": True,
        }
        reference = metadata.get("reference_stats")
        if reference:
            self._reference_features = None
        return True

    def bootstrap(self, n_samples: Optional[int] = None) -> Dict[str, Any]:
        features, labels = generate_labeled_features(
            n_samples or self.settings.bootstrap_samples,
            self.settings.bootstrap_fraud_rate,
            self.settings.random_state,
        )
        return self.train_model_sync(
            features, labels, force=True, training_source="synthetic"
        )

    def train_model_sync(
        self,
        training_data: Any,
        labels: Any = None,
        validation_data: Any = None,
        force: bool = True,
        training_source: str = "supplied",
    ) -> Dict[str, Any]:
        frame = (
            training_data
            if isinstance(training_data, pd.DataFrame)
            else pd.DataFrame(training_data)
        )
        target = None if labels is None else np.asarray(labels).astype(int).ravel()
        result: TrainingResult = train_ensemble(
            frame,
            target,
            validation=validation_data,
            model_config=self.model_config,
            settings=self.settings,
            training_source=training_source,
        )
        promoted = True
        champion_ap = None
        challenger_ap = result.metrics.get("average_precision")
        if not force and self.model_ready and result.holdout is not None:
            try:
                champion_scores = self.ensemble_model.predict(result.holdout[0])
                champion = classification_metrics(
                    result.holdout[1], champion_scores, self.settings.high_threshold
                )
                champion_ap = champion.get("average_precision")
                if champion_ap is not None and challenger_ap is not None:
                    promoted = (
                        challenger_ap >= champion_ap + self.settings.min_promotion_gain
                    )
            except Exception as exc:
                logger.warning(
                    "Champion evaluation failed, promoting challenger: %s", exc
                )
        version = None
        if promoted:
            self._install_model(result.model)
            now = datetime.now(timezone.utc)
            self.performance_metrics["last_retrain"] = now
            snapshot_frame = (
                result.model._clean(frame.copy())
                if result.model.feature_columns
                else frame
            )
            snapshot_target = target
            if snapshot_target is not None and len(snapshot_frame) > SNAPSHOT_LIMIT:
                keep = np.random.default_rng(self.settings.random_state).choice(
                    len(snapshot_frame), SNAPSHOT_LIMIT, replace=False
                )
                snapshot_frame = snapshot_frame.iloc[keep]
                snapshot_target = snapshot_target[keep]
            if snapshot_target is not None:
                self._snapshot = (
                    snapshot_frame.reset_index(drop=True),
                    snapshot_target,
                )
            self._reference_features = snapshot_frame.reset_index(drop=True).head(
                SNAPSHOT_LIMIT
            )
            self._recent_features.clear()
            self._last_drift = None
            self._feedback_since_train = 0
            version = self._persist(result, training_source)
            if version:
                self._loaded_registry_version = version
        summary = {
            "training_samples": len(frame),
            "model_version": result.model.model_version,
            "registry_version": version,
            "training_timestamp": result.model.training_timestamp,
            "training_source": training_source,
            "duration_seconds": round(result.duration_seconds, 3),
            "metrics": result.metrics,
            "holdout_samples": result.holdout_samples,
            "promoted": promoted,
            "champion_average_precision": champion_ap,
            "skipped_members": dict(result.model.skipped),
            "voting_strategy": result.model.voting_strategy,
        }
        self._last_training = {**summary, "loaded_from_registry": False}
        return summary

    def _persist(self, result: TrainingResult, source: str) -> Optional[str]:
        if self.registry is None:
            return None
        try:
            return self.registry.save(
                MODEL_NAME,
                result.model,
                {
                    "training_source": source,
                    "training_samples": result.training_samples,
                    "metrics": result.metrics,
                    "feature_columns": result.model.feature_columns,
                    "voting_strategy": result.model.voting_strategy,
                },
            )
        except Exception as exc:
            logger.error("Model persistence failed: %s", exc)
            return None

    async def train_model(
        self, training_data: Any, labels: Any = None, validation_data: Any = None
    ) -> Dict[str, Any]:
        return await asyncio.to_thread(
            self.train_model_sync,
            training_data,
            labels,
            validation_data,
            True,
            "supplied",
        )

    def train_from_transactions(
        self,
        transactions: List[Dict[str, Any]],
        label_key: str = "is_fraud",
        force: bool = True,
    ) -> Dict[str, Any]:
        features, labels = build_training_frame(transactions, label_key, self.settings)
        return self.train_model_sync(
            features, labels, force=force, training_source="transactions"
        )

    def refresh_model_if_stale(self, min_interval_seconds: float = 30.0) -> bool:
        if self.registry is None:
            return False
        now = time.monotonic()
        if now - self._last_refresh_check < min_interval_seconds:
            return False
        self._last_refresh_check = now
        try:
            current = self.registry.current_version(MODEL_NAME)
        except Exception:
            return False
        if not current or current == self._loaded_registry_version:
            return False
        return self.load_latest_model()

    def detect(
        self,
        transaction_data: Dict[str, Any],
        user_history: Any = None,
        record: bool = True,
    ) -> FraudAlert:
        self.refresh_model_if_stale()
        try:
            alert = self.real_time_detector.detect_fraud(transaction_data, user_history)
        except Exception:
            self.tracker.record_error()
            self.exporter.observe_error()
            raise
        mode = (alert.metadata or {}).get("mode", "rules_only")
        latency = float((alert.metadata or {}).get("latency_ms", 0.0))
        self.tracker.record(latency, alert.risk_score, alert.action.value, mode)
        self.exporter.observe(alert.action.value, mode, latency)
        if record:
            self._record(alert, transaction_data, user_history)
        return alert

    def _record(
        self, alert: FraudAlert, raw: Dict[str, Any], supplied_history: Any
    ) -> None:
        row = (alert.metadata or {}).get("feature_values", {})
        with self._lock:
            self.alerts_storage.append(alert)
            self._alerts_by_tx[alert.transaction_id] = alert
            while len(self._alerts_by_tx) > self.settings.alert_retention:
                self._alerts_by_tx.popitem(last=False)
            self._feature_cache[alert.transaction_id] = row
            while len(self._feature_cache) > self.settings.feature_cache_size:
                self._feature_cache.popitem(last=False)
            self._recent_features.append(row)
            self.performance_metrics["total_predictions"] += 1
            if alert.is_flagged:
                self.performance_metrics["fraud_detected"] += 1
        if supplied_history is None and alert.action != FraudAction.BLOCK:
            try:
                normalized = normalize_transaction(raw)
                self.history_store.append(alert.user_id, normalized)
            except Exception as exc:
                logger.warning("History update skipped: %s", exc)

    async def detect_fraud(
        self, transaction_data: Dict[str, Any], user_history: Any = None
    ) -> FraudAlert:
        return await asyncio.to_thread(self.detect, transaction_data, user_history)

    def batch_detect(
        self,
        transactions: Iterable[Dict[str, Any]],
        user_histories: Optional[Dict[str, Any]] = None,
    ) -> List[FraudAlert]:
        alerts = []
        for item in transactions:
            history = None
            if user_histories:
                history = user_histories.get(item.get("user_id"))
            alerts.append(self.detect(item, history))
        return alerts

    async def batch_detect_fraud(
        self,
        transactions: List[Dict[str, Any]],
        user_histories: Optional[Dict[str, Any]] = None,
    ) -> List[FraudAlert]:
        return await asyncio.to_thread(self.batch_detect, transactions, user_histories)

    def get_recent_alerts(
        self,
        hours: int = 24,
        risk_levels: Optional[List[RiskLevel]] = None,
        limit: int = 1000,
    ) -> List[FraudAlert]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        with self._lock:
            items = list(self.alerts_storage)
        recent = [a for a in items if a.timestamp >= cutoff]
        if risk_levels:
            recent = [a for a in recent if a.risk_level in risk_levels]
        recent.sort(key=lambda a: a.timestamp, reverse=True)
        return recent[:limit]

    def get_alert(self, alert_id: str) -> Optional[FraudAlert]:
        with self._lock:
            for alert in reversed(self.alerts_storage):
                if alert.alert_id == alert_id:
                    return alert
        return None

    def get_fraud_statistics(self, hours: int = 24) -> Dict[str, Any]:
        recent = self.get_recent_alerts(hours, limit=self.settings.alert_retention)
        if not recent:
            return {
                "total_transactions": 0,
                "fraud_detected": 0,
                "fraud_rate": 0.0,
                "risk_distribution": {level.value: 0 for level in RiskLevel},
                "fraud_types": {},
                "actions": {},
                "average_risk_score": 0.0,
            }
        flagged = [a for a in recent if a.is_flagged]
        fraud_types: Dict[str, int] = {}
        actions: Dict[str, int] = {}
        for alert in recent:
            actions[alert.action.value] = actions.get(alert.action.value, 0) + 1
            for kind in alert.fraud_types:
                fraud_types[kind.value] = fraud_types.get(kind.value, 0) + 1
        return {
            "total_transactions": len(recent),
            "fraud_detected": len(flagged),
            "fraud_rate": len(flagged) / len(recent),
            "risk_distribution": {
                level.value: sum(1 for a in recent if a.risk_level == level)
                for level in RiskLevel
            },
            "fraud_types": fraud_types,
            "actions": actions,
            "average_risk_score": float(np.mean([a.risk_score for a in recent])),
        }

    def record_feedback(
        self, transaction_id: str, is_fraud: bool, feedback_type: str = "manual_review"
    ) -> bool:
        with self._lock:
            alert = self._alerts_by_tx.get(transaction_id)
            if alert is None:
                return False
            metrics = self.performance_metrics
            predicted = alert.is_flagged
            if transaction_id in self._feedback:
                previous = self._feedback[transaction_id]
                key = self._confusion_key(predicted, previous)
                metrics[key] = max(0, metrics[key] - 1)
            else:
                row = self._feature_cache.get(transaction_id)
                if row:
                    self._feedback_rows.append(row)
                    self._feedback_labels.append(int(is_fraud))
                    self._feedback_since_train += 1
            if (
                transaction_id in self._feedback
                and transaction_id in self._feature_cache
            ):
                row = self._feature_cache[transaction_id]
                for index, existing in enumerate(self._feedback_rows):
                    if existing is row:
                        self._feedback_labels[index] = int(is_fraud)
                        break
            self._feedback[transaction_id] = bool(is_fraud)
            metrics[self._confusion_key(predicted, bool(is_fraud))] += 1
            return True

    @staticmethod
    def _confusion_key(predicted: bool, actual: bool) -> str:
        if predicted and actual:
            return "true_positives"
        if predicted and not actual:
            return "false_positives"
        if not predicted and actual:
            return "false_negatives"
        return "true_negatives"

    async def update_model_feedback(
        self, transaction_id: str, is_fraud: bool, feedback_type: str = "manual_review"
    ) -> bool:
        return self.record_feedback(transaction_id, is_fraud, feedback_type)

    def drift_report(self) -> Dict[str, Any]:
        if self._reference_features is None or not self._recent_features:
            return {
                "drifted": False,
                "reason": "insufficient_data",
                "samples": len(self._recent_features),
            }
        current = pd.DataFrame(list(self._recent_features))
        reference = self._reference_features
        columns = [c for c in current.columns if c in reference.columns]
        report = compute_drift(
            reference[columns], current[columns], self.settings.drift_psi_threshold
        )
        self._last_drift = report
        return report.to_dict()

    def retrain_reasons(self) -> List[str]:
        reasons: List[str] = []
        if not self.model_ready:
            reasons.append("no_trained_model")
            return reasons
        trained_at = self.ensemble_model.training_timestamp
        if trained_at:
            try:
                age = datetime.now(timezone.utc) - datetime.fromisoformat(trained_at)
                if age >= timedelta(days=self.retrain_threshold_days):
                    reasons.append("model_age_exceeded")
            except ValueError:
                pass
        if self._feedback_since_train >= self.settings.min_feedback_samples:
            reasons.append("feedback_volume_reached")
        if self.drift_report().get("drifted"):
            reasons.append("feature_drift_detected")
        return reasons

    async def check_retrain_needed(self) -> bool:
        return bool(self.retrain_reasons())

    def retrain_from_feedback(self, force: bool = False) -> Dict[str, Any]:
        with self._lock:
            rows = list(self._feedback_rows)
            labels = list(self._feedback_labels)
            snapshot = self._snapshot
        if snapshot is None and len(set(labels)) < 2:
            raise FraudDetectionError("Not enough labeled data to retrain")
        parts = []
        targets = []
        if snapshot is not None:
            parts.append(snapshot[0])
            targets.append(snapshot[1])
        if rows:
            feedback_frame = pd.DataFrame(rows)
            repeats = 3
            parts.extend([feedback_frame] * repeats)
            targets.extend([np.asarray(labels)] * repeats)
        features = pd.concat(parts, ignore_index=True)
        target = np.concatenate(targets)
        return self.train_model_sync(
            features, target, force=force, training_source="feedback"
        )

    def maybe_auto_retrain(self) -> Optional[Dict[str, Any]]:
        if not self.auto_retrain:
            return None
        if not self.retrain_reasons():
            return None
        try:
            return self.retrain_from_feedback(force=False)
        except FraudDetectionError as exc:
            logger.info("Auto retrain skipped: %s", exc)
            return None

    def evaluate(
        self, features: Any, labels: Any, threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        if not self.model_ready:
            raise FraudDetectionError("Model not trained")
        scores = self.ensemble_model.predict(features)
        return classification_metrics(
            labels, scores, threshold or self.settings.high_threshold
        )

    def get_model_status(self) -> Dict[str, Any]:
        model = self.ensemble_model
        metrics = dict(self.performance_metrics)
        last = metrics.get("last_retrain")
        metrics["last_retrain"] = (
            last.isoformat() if isinstance(last, datetime) else last
        )
        tp, fp, fn = (
            metrics["true_positives"],
            metrics["false_positives"],
            metrics["false_negatives"],
        )
        metrics["precision"] = tp / (tp + fp) if tp + fp else None
        metrics["recall"] = tp / (tp + fn) if tp + fn else None
        return {
            "model_initialized": model is not None,
            "model_trained": bool(model and model.is_trained),
            "real_time_detector_ready": self.real_time_detector is not None,
            "mode": "model" if self.model_ready else "rules_only",
            "performance_metrics": metrics,
            "model_version": model.model_version if model else None,
            "training_timestamp": model.training_timestamp if model else None,
            "training_source": model.training_source if model else None,
            "voting_strategy": model.voting_strategy if model else None,
            "individual_models": model.get_model_status() if model else {},
            "skipped_members": dict(model.skipped) if model else {},
            "last_training": self._last_training,
            "feedback_samples": len(self._feedback_rows),
            "auto_retrain": self.auto_retrain,
            "runtime": self.tracker.snapshot(),
        }

    def health(self) -> Dict[str, Any]:
        if not self.settings.enabled:
            return {"status": "disabled", "model_ready": False, "mode": "disabled"}
        ready = self.model_ready
        return {
            "status": "healthy" if ready else "degraded",
            "model_ready": ready,
            "mode": "model" if ready else "rules_only",
            "model_version": self.model_version() if ready else None,
        }

    def analyze_transaction(
        self, transaction_data: Dict[str, Any], user_history: Any = None
    ) -> Dict[str, Any]:
        alert = self.detect(transaction_data, user_history)
        return {
            "transaction_id": alert.transaction_id,
            "risk_score": alert.risk_score,
            "risk_level": alert.risk_level.value,
            "action": alert.action.value,
            "is_fraud": alert.is_flagged,
            "fraud_types": [t.value for t in alert.fraud_types],
            "recommended_actions": alert.recommended_actions,
            "explanation": alert.explanation,
            "approved": alert.action in (FraudAction.ALLOW, FraudAction.MONITOR),
            "flags": [hit["name"] for hit in alert.explanation.get("rule_hits", [])],
        }

    def detect_anomalies(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        tx = normalize_transaction(transaction_data)
        tx["_normalized"] = True
        features = self.feature_engineer.extract_transaction_features(tx, None)
        rule_score, hits = self.real_time_detector.rule_engine.evaluate(features)
        scores = [rule_score]
        if self.model_ready:
            try:
                row = self.feature_engineer.features_to_dataframe(features)
                members = self.ensemble_model.predict_members(row)
                anomaly = [
                    v[0]
                    for k, v in members.items()
                    if k in ("isolation_forest", "one_class_svm", "autoencoder")
                ]
                if anomaly:
                    scores.append(float(np.mean(anomaly)) * 0.8)
            except Exception as exc:
                logger.warning("Anomaly model scoring failed: %s", exc)
        score = float(
            min(max(scores) if len(scores) == 1 else combine_scores(scores), 1.0)
        )
        level = RiskLevel.from_score(
            score,
            self.settings.medium_threshold,
            self.settings.high_threshold,
            self.settings.critical_threshold,
        )
        anomalous = score > 0.7
        return {
            "anomaly_score": score,
            "risk_level": level.value,
            "is_anomaly": anomalous,
            "is_anomalous": anomalous,
            "rule_hits": [hit.to_dict() for hit in hits],
        }

    def check_velocity(
        self, user_id: str, transactions_or_amount: Any = None, currency: str = "USD"
    ) -> Dict[str, Any]:
        if isinstance(transactions_or_amount, list):
            transactions = transactions_or_amount
            total = sum(float(t.get("amount", 0) or 0) for t in transactions)
            count = len(transactions)
            frame = normalize_history(
                [
                    {"timestamp": t.get("timestamp"), "amount": t.get("amount", 0)}
                    for t in transactions
                    if t.get("timestamp")
                ]
            )
            burst = 0
            if not frame.empty:
                latest = frame["timestamp"].max()
                burst = int((frame["timestamp"] > latest - timedelta(hours=1)).sum())
            exceeded = (
                count >= 20
                or total >= 10000
                or burst >= self.real_time_detector.rule_engine.config.velocity_1h_limit
            )
            return {
                "user_id": user_id,
                "transaction_count": count,
                "total_amount": total,
                "transactions_last_hour": burst,
                "velocity_risk": "high" if exceeded else "low",
                "velocity_exceeded": exceeded,
                "transaction_count_24h": count,
            }
        amount = float(transactions_or_amount or 0)
        history = self.history_store.get(user_id)
        now = datetime.now(timezone.utc)
        recent = (
            history[history["timestamp"] > now - timedelta(hours=24)]
            if not history.empty
            else history
        )
        count = int(len(recent))
        total = float(recent["amount"].sum()) + amount if count else amount
        exceeded = count >= 20 or total >= 10000
        return {
            "user_id": user_id,
            "transaction_count_24h": count,
            "total_amount_24h": total,
            "velocity_exceeded": exceeded,
            "risk_level": "high" if exceeded else "low",
            "currency": currency,
        }


_service_lock = threading.Lock()
_service_instance: Optional[FraudDetectionService] = None


def get_fraud_service(config: Optional[Dict[str, Any]] = None) -> FraudDetectionService:
    global _service_instance
    if _service_instance is None:
        with _service_lock:
            if _service_instance is None:
                _service_instance = FraudDetectionService(config)
    return _service_instance


def reset_fraud_service() -> None:
    global _service_instance
    with _service_lock:
        _service_instance = None
