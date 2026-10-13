from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class QueryType(Enum):
    ACCOUNT_BALANCE = "account_balance"
    TRANSACTION_HISTORY = "transaction_history"
    SPENDING_ANALYSIS = "spending_analysis"
    SAVINGS_ADVICE = "savings_advice"
    CARD_MANAGEMENT = "card_management"
    PAYMENTS_TRANSFERS = "payments_transfers"
    FRAUD_SECURITY = "fraud_security"
    KYC_COMPLIANCE = "kyc_compliance"
    FEES_LIMITS = "fees_limits"
    TECHNICAL_SUPPORT = "technical_support"
    GREETING = "greeting"
    GENERAL = "general"


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def from_score(cls, score: float) -> "ConfidenceLevel":
        if score >= 0.7:
            return cls.HIGH
        if score >= 0.4:
            return cls.MEDIUM
        return cls.LOW


@dataclass
class ChatMessage:
    user_id: str
    content: str
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    response_text: str
    query_type: QueryType
    confidence: float
    confidence_level: ConfidenceLevel
    suggested_actions: List[str] = field(default_factory=list)
    escalate_to_human: bool = False
    sources: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    grounded_in_account_data: bool = False
    redactions: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response_text,
            "query_type": self.query_type.value,
            "confidence": round(self.confidence, 4),
            "confidence_level": self.confidence_level.value,
            "suggested_actions": self.suggested_actions,
            "escalate_to_human": self.escalate_to_human,
            "sources": self.sources,
            "session_id": self.session_id,
            "grounded_in_account_data": self.grounded_in_account_data,
            "timestamp": self.timestamp.isoformat(),
        }
