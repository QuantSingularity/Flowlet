import hashlib
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

_log_handlers = [logging.StreamHandler()]
_log_path = os.environ.get(
    "FRAUD_DETECTION_LOG_FILE", "/var/log/flowlet/fraud_detection.log"
)
try:
    os.makedirs(os.path.dirname(_log_path), exist_ok=True)
    _log_handlers.insert(0, logging.FileHandler(_log_path))
except OSError:
    # Log directory is not writable (e.g. local dev, CI, containers without the
    # mounted volume). Fall back to console-only logging instead of failing import.
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=_log_handlers,
)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk assessment levels for transactions"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudAction(Enum):
    """Actions to take based on fraud detection"""

    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"
    REQUIRE_2FA = "require_2fa"


@dataclass
class TransactionFeatures:
    """Transaction features for fraud detection"""

    amount: float
    merchant_category: str
    transaction_time: datetime
    location_country: str
    location_city: str
    card_present: bool
    online_transaction: bool
    user_id: str
    merchant_id: str
    previous_transaction_count_24h: int
    previous_transaction_amount_24h: float
    account_age_days: int
    velocity_score: float
    device_fingerprint: str
    ip_address: str
    time_since_last_transaction: int


@dataclass
class FraudDetectionResult:
    """Result of fraud detection analysis"""

    transaction_id: str
    risk_level: RiskLevel
    risk_score: float
    fraud_probability: float
    recommended_action: FraudAction
    explanation: Dict[str, float]
    model_version: str
    processing_time_ms: int
    timestamp: datetime


class ExplainableAIFraudDetector:
    """
    Advanced fraud detection system with explainable AI capabilities
    Meets financial industry standards for transparency and auditability
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        self.redis_client = redis_client or redis.Redis(
            host="localhost", port=6379, db=0
        )
        self.isolation_forest = None
        self.random_forest = None
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.model_version = "1.0.0"
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._load_models()
        self._initialize_feature_engineering()

    def _initialize_feature_engineering(self) -> Any:
        """Initialize feature engineering components"""
        self.velocity_calculator = VelocityCalculator(self.redis_client)
        self.device_profiler = DeviceProfiler(self.redis_client)
        self.location_analyzer = LocationAnalyzer()

    def _load_models(self) -> Any:
        """Load pre-trained models from disk"""
        try:
            self.isolation_forest = joblib.load("/models/isolation_forest.pkl")
            self.random_forest = joblib.load("/models/random_forest.pkl")
            self.scaler = joblib.load("/models/scaler.pkl")
            with open("/models/feature_importance.json", "r") as f:
                self.feature_importance = json.load(f)
            logger.info("Pre-trained models loaded successfully")
        except FileNotFoundError:
            logger.warning("No pre-trained models found. Will train new models.")
            self._train_initial_models()

    def _train_initial_models(self) -> Any:
        """Train initial models with synthetic data for demonstration"""
        synthetic_data = self._generate_synthetic_training_data(10000)
        X = synthetic_data.drop(["is_fraud", "transaction_id"], axis=1)
        y = synthetic_data["is_fraud"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        self.isolation_forest = IsolationForest(
            contamination=0.1, random_state=42, n_estimators=200
        )
        self.isolation_forest.fit(X_train_scaled)
        self.random_forest = RandomForestClassifier(
            n_estimators=200, max_depth=10, random_state=42, class_weight="balanced"
        )
        self.random_forest.fit(X_train_scaled, y_train)
        feature_names = X.columns.tolist()
        self.feature_importance = dict(
            zip(feature_names, self.random_forest.feature_importances_)
        )
        y_pred = self.random_forest.predict(X_test_scaled)
        y_pred_proba = self.random_forest.predict_proba(X_test_scaled)[:, 1]
        logger.info("Model training completed:")
        logger.info(f"AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
        logger.info(f"Classification Report:\n{classification_report(y_test, y_pred)}")
        self._save_models()

    def _generate_synthetic_training_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic training data for initial model training"""
        np.random.seed(42)
        data = []
        for i in range(n_samples):
            is_fraud = np.random.random() < 0.1
            if is_fraud:
                amount = np.random.lognormal(mean=6, sigma=2)
                velocity_score = np.random.uniform(0.7, 1.0)
                time_since_last = np.random.uniform(0, 30)
                previous_count_24h = np.random.randint(10, 50)
            else:
                amount = np.random.lognormal(mean=3, sigma=1)
                velocity_score = np.random.uniform(0.0, 0.3)
                time_since_last = np.random.uniform(60, 1440)
                previous_count_24h = np.random.randint(0, 5)
            transaction = {
                "transaction_id": f"txn_{i}",
                "amount": amount,
                "merchant_category_encoded": np.random.randint(0, 20),
                "card_present": np.random.choice([0, 1]),
                "online_transaction": np.random.choice([0, 1]),
                "previous_transaction_count_24h": previous_count_24h,
                "previous_transaction_amount_24h": amount * previous_count_24h,
                "account_age_days": np.random.randint(1, 3650),
                "velocity_score": velocity_score,
                "time_since_last_transaction": time_since_last,
                "location_risk_score": np.random.uniform(0, 1),
                "device_risk_score": np.random.uniform(0, 1),
                "hour_of_day": np.random.randint(0, 24),
                "day_of_week": np.random.randint(0, 7),
                "is_fraud": int(is_fraud),
            }
            data.append(transaction)
        return pd.DataFrame(data)

    def _save_models(self) -> Any:
        """Save trained models to disk"""
        os.makedirs("/models", exist_ok=True)
        joblib.dump(self.isolation_forest, "/models/isolation_forest.pkl")
        joblib.dump(self.random_forest, "/models/random_forest.pkl")
        joblib.dump(self.scaler, "/models/scaler.pkl")
        with open("/models/feature_importance.json", "w") as f:
            json.dump(self.feature_importance, f)
        logger.info("Models saved successfully")

    async def detect_fraud(
        self, transaction_features: TransactionFeatures
    ) -> FraudDetectionResult:
        """
        Detect fraud in a transaction with explainable results
        """
        start_time = datetime.now()
        transaction_id = self._generate_transaction_id(transaction_features)
        try:
            feature_vector = await self._extract_features(transaction_features)
            feature_vector_scaled = self.scaler.transform([feature_vector])
            anomaly_score = self.isolation_forest.decision_function(
                feature_vector_scaled
            )[0]
            fraud_probability = self.random_forest.predict_proba(feature_vector_scaled)[
                0
            ][1]
            risk_score = 0.4 * (1 - (anomaly_score + 1) / 2) + 0.6 * fraud_probability
            risk_level, recommended_action = self._determine_risk_and_action(risk_score)
            explanation = self._generate_explanation(feature_vector, fraud_probability)
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            result = FraudDetectionResult(
                transaction_id=transaction_id,
                risk_level=risk_level,
                risk_score=risk_score,
                fraud_probability=fraud_probability,
                recommended_action=recommended_action,
                explanation=explanation,
                model_version=self.model_version,
                processing_time_ms=processing_time,
                timestamp=datetime.now(timezone.utc),
            )
            await self._log_fraud_detection(result, transaction_features)
            await self._cache_result(result)
            return result
        except Exception as e:
            logger.error(f"Error in fraud detection: {str(e)}")
            return FraudDetectionResult(
                transaction_id=transaction_id,
                risk_level=RiskLevel.MEDIUM,
                risk_score=0.5,
                fraud_probability=0.5,
                recommended_action=FraudAction.REVIEW,
                explanation={"error": 1.0},
                model_version=self.model_version,
                processing_time_ms=int(
                    (datetime.now() - start_time).total_seconds() * 1000
                ),
                timestamp=datetime.now(timezone.utc),
            )

    async def _extract_features(
        self, transaction_features: TransactionFeatures
    ) -> List[float]:
        """Extract and engineer features for fraud detection"""
        features = [
            transaction_features.amount,
            self._encode_merchant_category(transaction_features.merchant_category),
            int(transaction_features.card_present),
            int(transaction_features.online_transaction),
            transaction_features.previous_transaction_count_24h,
            transaction_features.previous_transaction_amount_24h,
            transaction_features.account_age_days,
            transaction_features.velocity_score,
            transaction_features.time_since_last_transaction,
        ]
        location_risk = await self.location_analyzer.calculate_risk(
            transaction_features.location_country, transaction_features.location_city
        )
        features.append(location_risk)
        device_risk = await self.device_profiler.calculate_risk(
            transaction_features.device_fingerprint, transaction_features.user_id
        )
        features.append(device_risk)
        hour_of_day = transaction_features.transaction_time.hour
        day_of_week = transaction_features.transaction_time.weekday()
        features.extend([hour_of_day, day_of_week])
        return features

    def _encode_merchant_category(self, category: str) -> int:
        """Encode merchant category to numerical value"""
        category_mapping = {
            "grocery": 0,
            "gas": 1,
            "restaurant": 2,
            "retail": 3,
            "online": 4,
            "atm": 5,
            "pharmacy": 6,
            "hotel": 7,
            "airline": 8,
            "entertainment": 9,
            "other": 10,
        }
        return category_mapping.get(category.lower(), 10)

    def _determine_risk_and_action(
        self, risk_score: float
    ) -> Tuple[RiskLevel, FraudAction]:
        """Determine risk level and recommended action based on score"""
        if risk_score >= 0.8:
            return (RiskLevel.CRITICAL, FraudAction.BLOCK)
        elif risk_score >= 0.6:
            return (RiskLevel.HIGH, FraudAction.REQUIRE_2FA)
        elif risk_score >= 0.3:
            return (RiskLevel.MEDIUM, FraudAction.REVIEW)
        else:
            return (RiskLevel.LOW, FraudAction.ALLOW)

    def _generate_explanation(
        self, feature_vector: List[float], fraud_probability: float
    ) -> Dict[str, float]:
        """Generate explainable AI explanation for the fraud detection decision"""
        feature_names = [
            "amount",
            "merchant_category",
            "card_present",
            "online_transaction",
            "previous_count_24h",
            "previous_amount_24h",
            "account_age_days",
            "velocity_score",
            "time_since_last",
            "location_risk",
            "device_risk",
            "hour_of_day",
            "day_of_week",
        ]
        explanation = {}
        for i, (feature_name, value) in enumerate(zip(feature_names, feature_vector)):
            if feature_name in self.feature_importance:
                contribution = self.feature_importance[feature_name] * fraud_probability
                explanation[feature_name] = round(contribution, 4)
        return explanation

    def _generate_transaction_id(
        self, transaction_features: TransactionFeatures
    ) -> str:
        """Generate unique transaction ID for tracking"""
        data = f"{transaction_features.user_id}_{transaction_features.amount}_{transaction_features.transaction_time}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    async def _log_fraud_detection(
        self, result: FraudDetectionResult, features: TransactionFeatures
    ):
        """Log fraud detection result for audit trail"""
        log_entry = {
            "timestamp": result.timestamp.isoformat(),
            "transaction_id": result.transaction_id,
            "user_id": features.user_id,
            "amount": features.amount,
            "risk_level": result.risk_level.value,
            "risk_score": result.risk_score,
            "fraud_probability": result.fraud_probability,
            "recommended_action": result.recommended_action.value,
            "model_version": result.model_version,
            "processing_time_ms": result.processing_time_ms,
        }
        logger.info(f"Fraud detection completed: {json.dumps(log_entry)}")

    async def _cache_result(self, result: FraudDetectionResult):
        """Cache fraud detection result for quick retrieval"""
        try:
            cache_key = f"fraud_result:{result.transaction_id}"
            cache_data = {
                "risk_level": result.risk_level.value,
                "risk_score": result.risk_score,
                "recommended_action": result.recommended_action.value,
                "timestamp": result.timestamp.isoformat(),
            }
            self.redis_client.setex(cache_key, 86400, json.dumps(cache_data))
        except Exception as e:
            logger.warning(f"Failed to cache fraud detection result: {str(e)}")


class VelocityCalculator:
    """Calculate transaction velocity metrics"""

    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis_client = redis_client

    async def calculate_velocity(self, user_id: str, current_amount: float) -> float:
        """Calculate velocity score based on recent transaction patterns"""
        try:
            key = f"user_transactions:{user_id}"
            transactions = self.redis_client.lrange(key, 0, 100)
            if not transactions:
                return 0.0
            recent_amounts = []
            for txn_data in transactions:
                txn = json.loads(txn_data)
                txn_time = datetime.fromisoformat(txn["timestamp"])
                if (datetime.now() - txn_time).total_seconds() < 3600:
                    recent_amounts.append(txn["amount"])
            if not recent_amounts:
                return 0.0
            total_amount = sum(recent_amounts)
            avg_amount = total_amount / len(recent_amounts)
            velocity_score = min(
                1.0, current_amount / max(avg_amount, 1) * (len(recent_amounts) / 10)
            )
            return velocity_score
        except Exception as e:
            logger.warning(f"Error calculating velocity: {str(e)}")
            return 0.5


class DeviceProfiler:
    """Profile device behavior for fraud detection"""

    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis_client = redis_client

    async def calculate_risk(self, device_fingerprint: str, user_id: str) -> float:
        """Calculate device risk score"""
        try:
            known_devices_key = f"user_devices:{user_id}"
            known_devices = self.redis_client.smembers(known_devices_key)
            if device_fingerprint.encode() in known_devices:
                return 0.1
            device_users_key = f"device_users:{device_fingerprint}"
            device_users = self.redis_client.smembers(device_users_key)
            if len(device_users) > 5:
                return 0.9
            elif len(device_users) > 1:
                return 0.6
            else:
                return 0.3
        except Exception as e:
            logger.warning(f"Error calculating device risk: {str(e)}")
            return 0.5


class LocationAnalyzer:
    """Analyze transaction location for fraud detection"""

    def __init__(self) -> None:
        self.high_risk_countries = {"XX", "YY", "ZZ"}

    async def calculate_risk(self, country: str, city: str) -> float:
        """Calculate location-based risk score"""
        try:
            risk_score = 0.0
            if country in self.high_risk_countries:
                risk_score += 0.5
            return min(1.0, risk_score)
        except Exception as e:
            logger.warning(f"Error calculating location risk: {str(e)}")
            return 0.2


class ModelMonitor:
    """Monitor model performance and trigger retraining when needed"""

    def __init__(self, fraud_detector: ExplainableAIFraudDetector) -> None:
        self.fraud_detector = fraud_detector
        self.performance_threshold = 0.85

    async def monitor_performance(self):
        """Monitor model performance and trigger retraining if needed"""

    async def retrain_model(self):
        """Retrain the fraud detection model with new data"""


__all__ = [
    "ExplainableAIFraudDetector",
    "TransactionFeatures",
    "FraudDetectionResult",
    "RiskLevel",
    "FraudAction",
    "ModelMonitor",
]
