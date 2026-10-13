import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..config import MLSettings, get_settings
from ..core.enums import FraudAction, FraudType, RiskLevel
from ..core.exceptions import FraudDetectionError
from ..core.logging import get_logger
from ..data.validation import normalize_transaction
from ..features.engineering import FeatureEngineer
from ..features.history import HistoryStore
from .explainer import FraudExplainer
from .models.ensemble import EnsembleFraudModel
from .rules import RuleEngine
from .types import FraudAlert

logger = get_logger(__name__)

_FEATURE_TYPES = {
    "new_device": FraudType.ACCOUNT_TAKEOVER,
    "new_location": FraudType.ACCOUNT_TAKEOVER,
    "distinct_devices_7d": FraudType.ACCOUNT_TAKEOVER,
    "velocity_1h": FraudType.CARD_TESTING,
    "minutes_since_last_tx": FraudType.CARD_TESTING,
    "high_risk_country": FraudType.MONEY_LAUNDERING,
    "cross_border": FraudType.MONEY_LAUNDERING,
    "is_round_amount": FraudType.MONEY_LAUNDERING,
    "high_risk_merchant": FraudType.MERCHANT_FRAUD,
}

_COMPLIANCE_TYPES = {FraudType.MONEY_LAUNDERING, FraudType.SANCTIONS_EXPOSURE}


class RealTimeFraudDetector:
    def __init__(
        self,
        model_or_config: Any = None,
        settings: Optional[MLSettings] = None,
        feature_engineer: Optional[FeatureEngineer] = None,
        rule_engine: Optional[RuleEngine] = None,
        history_store: Optional[HistoryStore] = None,
        explainer: Optional[FraudExplainer] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.ensemble_model: Optional[EnsembleFraudModel] = (
            model_or_config if isinstance(model_or_config, EnsembleFraudModel) else None
        )
        self.config: Dict[str, Any] = (
            model_or_config if isinstance(model_or_config, dict) else {}
        )
        self.feature_engineer = feature_engineer or FeatureEngineer(self.settings)
        self.rule_engine = rule_engine or RuleEngine()
        self.history_store = history_store
        self.explainer = explainer or FraudExplainer(self.settings)

    def set_model(self, model: Optional[EnsembleFraudModel]) -> None:
        self.ensemble_model = model

    @property
    def model_ready(self) -> bool:
        return bool(self.ensemble_model and self.ensemble_model.is_trained)

    def _level(self, score: float) -> RiskLevel:
        return RiskLevel.from_score(
            score,
            self.settings.medium_threshold,
            self.settings.high_threshold,
            self.settings.critical_threshold,
        )

    def _calculate_risk_level(self, score: float) -> RiskLevel:
        return self._level(score)

    @staticmethod
    def _get_recommended_actions(level: RiskLevel, types: List[FraudType]) -> List[str]:
        if level == RiskLevel.CRITICAL:
            actions = [
                "block_transaction",
                "notify_user",
                "flag_for_review",
                "alert_compliance",
            ]
        elif level == RiskLevel.HIGH:
            actions = ["require_additional_auth", "notify_user", "flag_for_review"]
        elif level == RiskLevel.MEDIUM:
            actions = ["monitor_account", "log_for_review"]
        else:
            actions = ["allow_transaction"]
        if level.at_least(RiskLevel.MEDIUM) and any(
            t in _COMPLIANCE_TYPES for t in types
        ):
            if "alert_compliance" not in actions:
                actions.append("alert_compliance")
        return actions

    def _model_inference(
        self, row: Any
    ) -> Tuple[Optional[float], Dict[str, float], Dict[str, float]]:
        model = self.ensemble_model
        if model is None or not model.is_trained:
            return None, {}, {}
        try:
            combined, members = model.predict_with_details(row)
            score = float(np.clip(combined[0], 0.0, 1.0))
            member_scores = {name: float(values[0]) for name, values in members.items()}
            try:
                contributions = model.local_contributions(row)
            except Exception as exc:
                logger.warning("Contribution computation failed: %s", exc)
                contributions = {}
            return score, member_scores, contributions
        except Exception as exc:
            logger.error("Model inference failed, using rules only: %s", exc)
            return None, {}, {}

    @staticmethod
    def _infer_types(contributions: Dict[str, float]) -> List[FraudType]:
        ranked = sorted(contributions.items(), key=lambda item: -item[1])
        for name, value in ranked:
            if value <= 0:
                break
            if name in _FEATURE_TYPES:
                return [_FEATURE_TYPES[name]]
        return [FraudType.PAYMENT_FRAUD]

    @staticmethod
    def _confidence(score: float, members: Dict[str, float], model_used: bool) -> float:
        separation = min(abs(score - 0.45) / 0.55, 1.0)
        if model_used and len(members) > 1:
            agreement = 1.0 - min(1.0, float(np.std(list(members.values()))) * 2.0)
        else:
            agreement = 0.8
        return float(np.clip(0.5 + 0.5 * separation * agreement, 0.5, 1.0))

    def detect_fraud(
        self, transaction_data: Dict[str, Any], user_history: Any = None
    ) -> FraudAlert:
        started = time.perf_counter()
        try:
            tx = normalize_transaction(transaction_data)
            tx["_normalized"] = True
            history = user_history
            if history is None and self.history_store is not None:
                history = self.history_store.get(tx["user_id"])
            features = self.feature_engineer.extract_transaction_features(tx, history)
            rule_score, hits = self.rule_engine.evaluate(features)
            row = self.feature_engineer.features_to_dataframe(features)
            model_score, members, contributions = self._model_inference(row)
            model_used = model_score is not None
            risk_score = max(model_score, rule_score) if model_used else rule_score
            risk_score = float(np.clip(risk_score, 0.0, 1.0))
            level = self._level(risk_score)
            fraud_types: List[FraudType] = []
            for hit in hits:
                if hit.fraud_type not in fraud_types:
                    fraud_types.append(hit.fraud_type)
            if level.at_least(RiskLevel.HIGH) and not fraud_types:
                fraud_types = self._infer_types(contributions)
            importance = (
                self.ensemble_model.get_feature_importance() if model_used else {}
            )
            explanation = self.explainer.explain_prediction(
                features, risk_score, importance, contributions, hits, members
            )
            version = self.ensemble_model.model_version if model_used else "rules-1.0"
            latency_ms = (time.perf_counter() - started) * 1000.0
            return FraudAlert(
                alert_id=str(uuid.uuid4()),
                transaction_id=tx["transaction_id"],
                user_id=tx["user_id"],
                risk_score=risk_score,
                risk_level=level,
                fraud_types=fraud_types,
                confidence=self._confidence(risk_score, members, model_used),
                timestamp=datetime.now(timezone.utc),
                features_used=list(importance.keys()) or list(row.columns),
                model_version=version,
                explanation=explanation,
                recommended_actions=self._get_recommended_actions(level, fraud_types),
                metadata={
                    "mode": "model" if model_used else "rules_only",
                    "model_score": model_score,
                    "rule_score": round(rule_score, 4),
                    "feature_values": {k: float(v) for k, v in row.iloc[0].items()},
                    "latency_ms": round(latency_ms, 3),
                    "amount": tx["amount"],
                    "currency": tx["currency"],
                },
                action=FraudAction.for_level(level),
            )
        except FraudDetectionError:
            raise
        except Exception as exc:
            logger.error("Real-time fraud detection failed: %s", exc)
            raise FraudDetectionError(f"Fraud detection failed: {exc}") from exc

    def check_transaction(
        self, transaction_data: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        alert = self.detect_fraud(transaction_data)
        return alert.is_flagged, alert.risk_score, alert.risk_level.value
