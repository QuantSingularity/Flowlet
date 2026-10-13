from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.enums import FraudAction, FraudType, RiskLevel


@dataclass
class RuleHit:
    name: str
    score: float
    fraud_type: FraudType
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 4),
            "fraud_type": self.fraud_type.value,
            "description": self.description,
            "evidence": self.evidence,
        }


@dataclass
class FraudAlert:
    alert_id: str
    transaction_id: str
    user_id: str
    risk_score: float
    risk_level: RiskLevel
    fraud_types: List[FraudType]
    confidence: float
    timestamp: datetime
    features_used: List[str]
    model_version: str
    explanation: Dict[str, Any]
    recommended_actions: List[str]
    metadata: Optional[Dict[str, Any]] = None
    action: FraudAction = FraudAction.ALLOW

    @property
    def is_flagged(self) -> bool:
        return self.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def to_dict(self, include_details: bool = True) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "alert_id": self.alert_id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "risk_score": round(float(self.risk_score), 6),
            "risk_level": self.risk_level.value,
            "action": self.action.value,
            "fraud_types": [item.value for item in self.fraud_types],
            "confidence": round(float(self.confidence), 6),
            "timestamp": self.timestamp.isoformat(),
            "recommended_actions": list(self.recommended_actions),
            "model_version": self.model_version,
        }
        if include_details:
            data["features_used"] = list(self.features_used)
            data["explanation"] = self.explanation
            data["metadata"] = self.metadata or {}
        return data
