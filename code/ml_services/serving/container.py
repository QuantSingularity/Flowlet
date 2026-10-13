import threading
from typing import Any, Dict, Optional

from ..config import MLSettings, get_settings
from ..core.logging import get_logger
from ..fraud_detection.service import FraudDetectionService, get_fraud_service
from ..risk_assessment.assessor import AIRiskAssessor
from ..support_chatbot.chatbot import FlowletAIChatbot
from ..transaction_intelligence.categorizer import AITransactionCategorizer
from ..transaction_intelligence.spending import SpendingAnalyzer

logger = get_logger(__name__)


class MLServiceContainer:
    def __init__(self, settings: Optional[MLSettings] = None) -> None:
        self.settings = settings or get_settings()
        self._lock = threading.RLock()
        self._fraud: Optional[FraudDetectionService] = None
        self._risk: Optional[AIRiskAssessor] = None
        self._categorizer: Optional[AITransactionCategorizer] = None
        self._spending: Optional[SpendingAnalyzer] = None
        self._chatbot: Optional[FlowletAIChatbot] = None

    @property
    def fraud(self) -> FraudDetectionService:
        if self._fraud is None:
            with self._lock:
                if self._fraud is None:
                    self._fraud = get_fraud_service()
        return self._fraud

    @property
    def risk(self) -> AIRiskAssessor:
        if self._risk is None:
            with self._lock:
                if self._risk is None:
                    self._risk = AIRiskAssessor()
        return self._risk

    @property
    def categorizer(self) -> AITransactionCategorizer:
        if self._categorizer is None:
            with self._lock:
                if self._categorizer is None:
                    self._categorizer = AITransactionCategorizer()
        return self._categorizer

    @property
    def spending(self) -> SpendingAnalyzer:
        if self._spending is None:
            with self._lock:
                if self._spending is None:
                    self._spending = SpendingAnalyzer(self.categorizer)
        return self._spending

    @property
    def chatbot(self) -> FlowletAIChatbot:
        if self._chatbot is None:
            with self._lock:
                if self._chatbot is None:
                    self._chatbot = FlowletAIChatbot()
        return self._chatbot

    def warm_up(self, block: bool = False) -> None:
        if not self.settings.enabled:
            return
        self.fraud.warm_up(block=block)

    def health(self) -> Dict[str, Any]:
        fraud = self.fraud.health()
        return {
            "enabled": self.settings.enabled,
            "status": fraud["status"],
            "environment": self.settings.environment,
            "fraud_detection": fraud,
            "components": {
                "risk_assessment": "ready",
                "transaction_intelligence": "ready",
                "support_chatbot": "ready",
            },
        }


_container_lock = threading.Lock()
_container: Optional[MLServiceContainer] = None


def get_container() -> MLServiceContainer:
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = MLServiceContainer()
    return _container


def reset_container() -> None:
    global _container
    with _container_lock:
        _container = None
