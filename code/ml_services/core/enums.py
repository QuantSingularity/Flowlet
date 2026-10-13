from enum import Enum
from typing import Optional


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(
        cls,
        score: float,
        medium: float = 0.3,
        high: float = 0.6,
        critical: float = 0.8,
    ) -> "RiskLevel":
        if score >= critical:
            return cls.CRITICAL
        if score >= high:
            return cls.HIGH
        if score >= medium:
            return cls.MEDIUM
        return cls.LOW

    @property
    def rank(self) -> int:
        return _RISK_RANK[self]

    def at_least(self, other: "RiskLevel") -> bool:
        return self.rank >= other.rank


_RISK_RANK = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


class FraudType(Enum):
    ACCOUNT_TAKEOVER = "account_takeover"
    IDENTITY_THEFT = "identity_theft"
    PAYMENT_FRAUD = "payment_fraud"
    CARD_FRAUD = "card_fraud"
    CARD_TESTING = "card_testing"
    MONEY_LAUNDERING = "money_laundering"
    SYNTHETIC_IDENTITY = "synthetic_identity"
    FIRST_PARTY_FRAUD = "first_party_fraud"
    MERCHANT_FRAUD = "merchant_fraud"
    APPLICATION_FRAUD = "application_fraud"
    SANCTIONS_EXPOSURE = "sanctions_exposure"


class FraudAction(Enum):
    ALLOW = "allow"
    MONITOR = "monitor"
    REVIEW = "review"
    CHALLENGE = "challenge"
    BLOCK = "block"

    @classmethod
    def for_level(cls, level: RiskLevel) -> "FraudAction":
        return _ACTION_BY_LEVEL[level]


_ACTION_BY_LEVEL = {
    RiskLevel.LOW: FraudAction.ALLOW,
    RiskLevel.MEDIUM: FraudAction.MONITOR,
    RiskLevel.HIGH: FraudAction.CHALLENGE,
    RiskLevel.CRITICAL: FraudAction.BLOCK,
}


class ModelType(Enum):
    ISOLATION_FOREST = "isolation_forest"
    ONE_CLASS_SVM = "one_class_svm"
    AUTOENCODER = "autoencoder"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"


def parse_risk_level(value: Optional[str]) -> Optional[RiskLevel]:
    if value is None:
        return None
    try:
        return RiskLevel(str(value).lower())
    except ValueError:
        return None
