from typing import Any, Dict, List, Optional

from ..config import MLSettings, get_settings
from ..core.enums import RiskLevel
from ..features.schema import FEATURE_DESCRIPTIONS
from ..features.types import TransactionFeatures
from .types import RuleHit


class FraudExplainer:
    def __init__(self, settings: Optional[MLSettings] = None) -> None:
        self.settings = settings or get_settings()

    def explain_prediction(
        self,
        features: TransactionFeatures,
        risk_score: float,
        feature_importance: Dict[str, float],
        contributions: Optional[Dict[str, float]] = None,
        rule_hits: Optional[List[RuleHit]] = None,
        member_scores: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        explanation: Dict[str, Any] = {
            "risk_score": risk_score,
            "primary_risk_factors": [],
            "contributing_factors": [],
            "protective_factors": [],
            "rule_hits": [hit.to_dict() for hit in (rule_hits or [])],
            "model_scores": {
                k: round(float(v), 4) for k, v in (member_scores or {}).items()
            },
            "summary": "",
        }
        if contributions:
            self._from_contributions(
                features, contributions, feature_importance, explanation
            )
        else:
            self._from_importance(features, feature_importance, explanation)
        explanation["summary"] = self._summary(risk_score, rule_hits or [])
        return explanation

    def _from_contributions(
        self,
        features: TransactionFeatures,
        contributions: Dict[str, float],
        importance: Dict[str, float],
        explanation: Dict[str, Any],
    ) -> None:
        positive = sorted(
            ((k, v) for k, v in contributions.items() if v > 0),
            key=lambda item: item[1],
            reverse=True,
        )
        negative = sorted(
            ((k, v) for k, v in contributions.items() if v < 0),
            key=lambda item: item[1],
        )
        mass = sum(v for _, v in positive) or 1.0
        for index, (name, value) in enumerate(positive[:8]):
            entry = self._entry(features, name, importance.get(name, 0.0), value)
            if entry is None:
                continue
            bucket = (
                "primary_risk_factors"
                if index < 3 and value / mass >= 0.1
                else "contributing_factors"
            )
            explanation[bucket].append(entry)
        for name, value in negative[:3]:
            entry = self._entry(features, name, importance.get(name, 0.0), value)
            if entry is not None:
                explanation["protective_factors"].append(entry)

    def _from_importance(
        self,
        features: TransactionFeatures,
        importance: Dict[str, float],
        explanation: Dict[str, Any],
    ) -> None:
        for name, weight in sorted(importance.items(), key=lambda item: -item[1]):
            if weight <= 0.1:
                continue
            value = getattr(features, name, None)
            if not value:
                continue
            entry = self._entry(features, name, weight, None)
            if entry is not None:
                explanation["primary_risk_factors"].append(entry)

    def _entry(
        self,
        features: TransactionFeatures,
        name: str,
        importance: float,
        contribution: Optional[float],
    ) -> Optional[Dict[str, Any]]:
        value = getattr(features, name, None)
        if value is None:
            return None
        entry: Dict[str, Any] = {
            "feature": name,
            "value": value if not isinstance(value, bool) else bool(value),
            "importance": round(float(importance), 4),
            "description": self._describe(name, value),
        }
        if contribution is not None:
            entry["contribution"] = round(float(contribution), 4)
        return entry

    @staticmethod
    def _describe(name: str, value: Any) -> str:
        template = FEATURE_DESCRIPTIONS.get(name)
        if template is None:
            return f"{name}: {value}"
        if isinstance(value, bool):
            return template if value else f"No: {template}"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return f"{name}: {value}"
        return template.format(value=number, abs_value=abs(number))

    def _summary(self, risk_score: float, hits: List[RuleHit]) -> str:
        level = RiskLevel.from_score(
            risk_score,
            self.settings.medium_threshold,
            self.settings.high_threshold,
            self.settings.critical_threshold,
        )
        text = {
            RiskLevel.CRITICAL: "High fraud risk detected due to multiple suspicious indicators",
            RiskLevel.HIGH: "Elevated fraud risk, additional verification recommended",
            RiskLevel.MEDIUM: "Moderate fraud risk, monitor transaction",
            RiskLevel.LOW: "Low fraud risk, transaction appears normal",
        }[level]
        if hits and level.at_least(RiskLevel.MEDIUM):
            text += f" ({', '.join(hit.name for hit in hits[:3])})"
        return text
