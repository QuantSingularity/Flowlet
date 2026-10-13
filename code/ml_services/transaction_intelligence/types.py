from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TransactionCategory(Enum):
    GROCERIES = "groceries"
    RESTAURANTS = "restaurants"
    GAS_STATIONS = "gas_stations"
    RETAIL_SHOPPING = "retail_shopping"
    ONLINE_SHOPPING = "online_shopping"
    ENTERTAINMENT = "entertainment"
    TRAVEL = "travel"
    TRANSPORTATION = "transportation"
    HEALTHCARE = "healthcare"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    EDUCATION = "education"
    PROFESSIONAL_SERVICES = "professional_services"
    HOME_IMPROVEMENT = "home_improvement"
    PERSONAL_CARE = "personal_care"
    CHARITY = "charity"
    INVESTMENTS = "investments"
    TRANSFERS = "transfers"
    ATM_WITHDRAWALS = "atm_withdrawals"
    FEES = "fees"
    INCOME = "income"
    REFUNDS = "refunds"
    OTHER = "other"


class SpendingPattern(Enum):
    REGULAR = "regular"
    SEASONAL = "seasonal"
    INCREASING = "increasing"
    DECREASING = "decreasing"
    VOLATILE = "volatile"
    STABLE = "stable"


@dataclass
class TransactionInsight:
    transaction_id: str
    category: TransactionCategory
    confidence: float
    subcategory: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_recurring: bool = False
    anomaly_score: float = 0.0
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    method: str = "rules"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "category": self.category.value,
            "confidence": round(self.confidence, 4),
            "subcategory": self.subcategory,
            "tags": self.tags,
            "is_recurring": self.is_recurring,
            "anomaly_score": round(self.anomaly_score, 4),
            "insights": self.insights,
            "recommendations": self.recommendations,
            "method": self.method,
        }


@dataclass
class SpendingAnalysis:
    user_id: str
    period_days: int
    total_spent: float
    total_income: float
    net_cash_flow: float
    category_totals: Dict[str, float]
    category_shares: Dict[str, float]
    monthly_trend: float
    pattern: SpendingPattern
    recurring: List[Dict[str, Any]]
    budget_recommendations: Dict[str, float]
    insights: List[str]
    alerts: List[str]
    forecast: Dict[str, Any]
    transaction_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "period_days": self.period_days,
            "total_spent": round(self.total_spent, 2),
            "total_income": round(self.total_income, 2),
            "net_cash_flow": round(self.net_cash_flow, 2),
            "category_totals": {
                k: round(v, 2) for k, v in self.category_totals.items()
            },
            "category_shares": {
                k: round(v, 4) for k, v in self.category_shares.items()
            },
            "monthly_trend": round(self.monthly_trend, 4),
            "pattern": self.pattern.value,
            "recurring": self.recurring,
            "budget_recommendations": {
                k: round(v, 2) for k, v in self.budget_recommendations.items()
            },
            "insights": self.insights,
            "alerts": self.alerts,
            "forecast": self.forecast,
            "transaction_count": self.transaction_count,
        }
