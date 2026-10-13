from .categorizer import AITransactionCategorizer
from .spending import SpendingAnalyzer, detect_recurring, forecast_spending
from .types import (
    SpendingAnalysis,
    SpendingPattern,
    TransactionCategory,
    TransactionInsight,
)

ai_categorizer = AITransactionCategorizer()

__all__ = [
    "AITransactionCategorizer",
    "SpendingAnalysis",
    "SpendingAnalyzer",
    "SpendingPattern",
    "TransactionCategory",
    "TransactionInsight",
    "ai_categorizer",
    "detect_recurring",
    "forecast_spending",
]
