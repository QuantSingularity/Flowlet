from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class RiskCategory(Enum):
    CREDIT_RISK = "credit_risk"
    FRAUD_RISK = "fraud_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    OPERATIONAL_RISK = "operational_risk"
    COMPLIANCE_RISK = "compliance_risk"


class RiskTier(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: float) -> "RiskTier":
        if score < 0.2:
            return cls.VERY_LOW
        if score < 0.4:
            return cls.LOW
        if score < 0.6:
            return cls.MEDIUM
        if score < 0.8:
            return cls.HIGH
        if score < 0.9:
            return cls.VERY_HIGH
        return cls.CRITICAL


@dataclass
class RiskFactor:
    factor_name: str
    category: RiskCategory
    weight: float
    score: float
    description: str
    impact: str
    mitigation_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_name": self.factor_name,
            "category": self.category.value,
            "weight": self.weight,
            "score": round(self.score, 4),
            "description": self.description,
            "impact": self.impact,
            "mitigation_suggestions": self.mitigation_suggestions,
        }


@dataclass
class RiskAssessment:
    user_id: str
    assessment_id: str
    timestamp: datetime
    overall_risk_score: float
    overall_risk_level: RiskTier
    risk_factors: List[RiskFactor]
    category_scores: Dict[str, float]
    predictions: Dict[str, Any]
    recommendations: List[str]
    monitoring_alerts: List[str]
    confidence_score: float
    data_completeness: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "assessment_id": self.assessment_id,
            "timestamp": self.timestamp.isoformat(),
            "overall_risk_score": round(self.overall_risk_score, 4),
            "overall_risk_level": self.overall_risk_level.value,
            "risk_factors": [factor.to_dict() for factor in self.risk_factors],
            "category_scores": {
                k: round(v, 4) for k, v in self.category_scores.items()
            },
            "predictions": self.predictions,
            "recommendations": self.recommendations,
            "monitoring_alerts": self.monitoring_alerts,
            "confidence_score": round(self.confidence_score, 4),
            "data_completeness": self.data_completeness,
        }
