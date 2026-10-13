import re
import threading
import uuid
from collections import Counter, defaultdict, deque
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.logging import get_logger
from .knowledge import DEFAULT_KNOWLEDGE_BASE, ESCALATION_PATTERN, INTENT_PATTERNS
from .privacy import redact_pii
from .types import ChatMessage, ChatResponse, ConfidenceLevel, QueryType

logger = get_logger(__name__)

SESSION_TURNS = 10
MAX_SESSIONS = 5000
MAX_MESSAGE_LENGTH = 2000
_INTENT_ORDER = [
    "fraud_security",
    "greeting",
    "account_balance",
    "transaction_history",
    "savings_advice",
    "spending_analysis",
    "card_management",
    "payments_transfers",
    "kyc_compliance",
    "fees_limits",
    "technical_support",
]
_INTENT_DOCS = {
    QueryType.CARD_MANAGEMENT: {"cards"},
    QueryType.PAYMENTS_TRANSFERS: {"send_money", "receive_money"},
    QueryType.FRAUD_SECURITY: {"fraud_alerts", "disputes", "lost_card"},
    QueryType.KYC_COMPLIANCE: {"kyc"},
    QueryType.FEES_LIMITS: {"limits_fees", "currencies"},
    QueryType.TECHNICAL_SUPPORT: {"login_issues", "security"},
    QueryType.SPENDING_ANALYSIS: {"budgeting"},
    QueryType.SAVINGS_ADVICE: {"budgeting"},
    QueryType.ACCOUNT_BALANCE: {"wallets"},
    QueryType.TRANSACTION_HISTORY: {"statements"},
}
_COMPILED = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in INTENT_PATTERNS.items()
}
_ESCALATION = re.compile(ESCALATION_PATTERN, re.IGNORECASE)

_SUGGESTED = {
    QueryType.ACCOUNT_BALANCE: ["View wallet", "Add funds"],
    QueryType.TRANSACTION_HISTORY: ["Open transactions", "Filter by date"],
    QueryType.SPENDING_ANALYSIS: ["Open analytics", "Set a budget"],
    QueryType.SAVINGS_ADVICE: ["Open budgeting", "Review recurring payments"],
    QueryType.CARD_MANAGEMENT: ["Open cards", "Freeze card"],
    QueryType.PAYMENTS_TRANSFERS: ["Send money", "View limits"],
    QueryType.FRAUD_SECURITY: ["Freeze card", "Review alerts", "Contact support"],
    QueryType.KYC_COMPLIANCE: ["Open verification"],
    QueryType.FEES_LIMITS: ["View limits"],
    QueryType.TECHNICAL_SUPPORT: ["Reset password", "Contact support"],
    QueryType.GREETING: ["Check balance", "Spending summary"],
    QueryType.GENERAL: ["Contact support"],
}


def _money(value: float, currency: str) -> str:
    return f"{value:,.2f} {currency}"


class ChatbotAnalytics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total = 0
        self.escalations = 0
        self.grounded = 0
        self.by_type: Counter = Counter()
        self.by_confidence: Counter = Counter()

    def update_stats(self, response: ChatResponse) -> None:
        with self._lock:
            self.total += 1
            self.escalations += int(response.escalate_to_human)
            self.grounded += int(response.grounded_in_account_data)
            self.by_type[response.query_type.value] += 1
            self.by_confidence[response.confidence_level.value] += 1

    def get_performance_report(self) -> Dict[str, Any]:
        with self._lock:
            total = self.total or 1
            return {
                "total_messages": self.total,
                "escalation_rate": self.escalations / total,
                "grounded_rate": self.grounded / total,
                "by_query_type": dict(self.by_type),
                "by_confidence": dict(self.by_confidence),
            }


class FlowletAIChatbot:
    def __init__(self, knowledge_base: Optional[List[Dict[str, str]]] = None) -> None:
        self.knowledge_base = list(knowledge_base or DEFAULT_KNOWLEDGE_BASE)
        self.analytics = ChatbotAnalytics()
        self._sessions: Dict[str, Deque[Tuple[str, QueryType]]] = defaultdict(
            lambda: deque(maxlen=SESSION_TURNS)
        )
        self._session_order: Deque[str] = deque()
        self._lock = threading.Lock()
        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), sublinear_tf=True, stop_words="english"
        )
        documents = [
            f"{item['title']} {item['keywords']} {item['content']}"
            for item in self.knowledge_base
        ]
        self._matrix = self._vectorizer.fit_transform(documents)

    def classify_intent(
        self, text: str, previous: Optional[QueryType] = None
    ) -> Tuple[QueryType, float]:
        for name in _INTENT_ORDER:
            if _COMPILED[name].search(text):
                return QueryType(name), 0.85
        words = text.split()
        if previous is not None and len(words) <= 4 and previous != QueryType.GREETING:
            return previous, 0.5
        return QueryType.GENERAL, 0.3

    def retrieve(
        self, text: str, top_k: int = 3, query_type: Optional[QueryType] = None
    ) -> List[Tuple[Dict[str, str], float]]:
        if not text.strip():
            return []
        similarities = cosine_similarity(
            self._vectorizer.transform([text]), self._matrix
        )[0].copy()
        preferred = _INTENT_DOCS.get(query_type, set()) if query_type else set()
        for index, item in enumerate(self.knowledge_base):
            if item["id"] in preferred and similarities[index] > 0:
                similarities[index] += 0.2
        order = np.argsort(similarities)[::-1][:top_k]
        found = [
            (self.knowledge_base[int(i)], float(similarities[int(i)]))
            for i in order
            if similarities[int(i)] > 0.05
        ]
        if not found and preferred:
            for item in self.knowledge_base:
                if item["id"] in preferred:
                    return [(item, 0.2)]
        return found

    def _remember(self, session_id: str, text: str, query_type: QueryType) -> None:
        with self._lock:
            if session_id not in self._sessions:
                self._session_order.append(session_id)
                while len(self._session_order) > MAX_SESSIONS:
                    self._sessions.pop(self._session_order.popleft(), None)
            self._sessions[session_id].append((text, query_type))

    def _previous(self, session_id: str) -> Optional[QueryType]:
        with self._lock:
            turns = self._sessions.get(session_id)
            return turns[-1][1] if turns else None

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def respond(
        self,
        user_id: str,
        text: str,
        session_id: Optional[str] = None,
        account_context: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        session_id = session_id or f"{user_id}:{uuid.uuid4().hex[:8]}"
        clean, redactions = redact_pii((text or "")[:MAX_MESSAGE_LENGTH].strip())
        if not clean:
            return self._finalize(
                ChatResponse(
                    "Please type a question and I will do my best to help.",
                    QueryType.GENERAL,
                    0.3,
                    ConfidenceLevel.LOW,
                    _SUGGESTED[QueryType.GENERAL],
                    session_id=session_id,
                    redactions=redactions,
                )
            )
        query_type, intent_confidence = self.classify_intent(
            clean, self._previous(session_id)
        )
        escalate = bool(_ESCALATION.search(clean))
        grounded_text, grounded = self._grounded_answer(
            query_type, account_context or {}
        )
        retrieved = self.retrieve(clean, query_type=query_type)
        sources = [item["id"] for item, _ in retrieved[:2]]
        if grounded_text:
            body = grounded_text
            confidence = max(intent_confidence, 0.8)
        elif query_type == QueryType.GREETING:
            body = "Hello. I can help with balances, spending insights, cards, transfers, and account questions. What would you like to know?"
            confidence = 0.9
            sources = []
        elif retrieved:
            best_item, best_score = retrieved[0]
            body = best_item["content"]
            confidence = float(
                min(
                    0.35
                    + best_score * 1.2
                    + (0.15 if intent_confidence >= 0.85 else 0.0),
                    0.95,
                )
            )
        else:
            body = "I could not find a confident answer to that. I can connect you with support if you would like."
            confidence = 0.2
        if (
            query_type
            in (
                QueryType.ACCOUNT_BALANCE,
                QueryType.TRANSACTION_HISTORY,
                QueryType.SPENDING_ANALYSIS,
                QueryType.SAVINGS_ADVICE,
            )
            and not grounded
        ):
            body = (
                "I do not have your latest account data in this conversation, so open the relevant page to see exact figures. "
                + body
            )
            confidence = min(confidence, 0.6)
        if query_type == QueryType.FRAUD_SECURITY or escalate:
            body += " If you see activity you do not recognize, freeze your card now and contact support so a specialist can review it."
            escalate = True
        if confidence < 0.3:
            escalate = True
        response = ChatResponse(
            response_text=body,
            query_type=query_type,
            confidence=confidence,
            confidence_level=ConfidenceLevel.from_score(confidence),
            suggested_actions=list(
                _SUGGESTED.get(query_type, _SUGGESTED[QueryType.GENERAL])
            ),
            escalate_to_human=escalate,
            sources=sources,
            session_id=session_id,
            grounded_in_account_data=grounded,
            redactions=redactions,
        )
        self._remember(session_id, clean, query_type)
        return self._finalize(response)

    def _finalize(self, response: ChatResponse) -> ChatResponse:
        self.analytics.update_stats(response)
        return response

    async def process_message(self, message: ChatMessage) -> ChatResponse:
        return self.respond(
            message.user_id, message.content, message.session_id, message.context
        )

    def _grounded_answer(
        self, query_type: QueryType, context: Dict[str, Any]
    ) -> Tuple[Optional[str], bool]:
        currency = str(context.get("currency") or "USD")
        if query_type == QueryType.ACCOUNT_BALANCE:
            balances = context.get("balances")
            total = context.get("total_balance")
            if isinstance(balances, dict) and balances:
                parts = [
                    _money(float(value), str(code)) for code, value in balances.items()
                ]
                return "Your current balances are " + ", ".join(parts) + ".", True
            if total is not None:
                return (
                    f"Your current balance is {_money(float(total), currency)}.",
                    True,
                )
        if query_type == QueryType.TRANSACTION_HISTORY:
            recent = context.get("recent_transactions") or []
            if recent:
                lines = []
                for tx in recent[:5]:
                    label = (
                        tx.get("description")
                        or tx.get("merchant_name")
                        or "Transaction"
                    )
                    sign = (
                        "+"
                        if str(tx.get("type", "")).lower()
                        in {"credit", "deposit", "income", "refund"}
                        else "-"
                    )
                    lines.append(
                        f"{label} ({sign}{_money(abs(float(tx.get('amount') or 0)), str(tx.get('currency') or currency))})"
                    )
                return (
                    "Your most recent transactions are " + "; ".join(lines) + ".",
                    True,
                )
        if query_type in (QueryType.SPENDING_ANALYSIS, QueryType.SAVINGS_ADVICE):
            summary = context.get("spending_summary")
            if isinstance(summary, dict) and summary.get("total_spent") is not None:
                return self._spending_text(query_type, summary, currency), True
        return None, False

    @staticmethod
    def _spending_text(
        query_type: QueryType, summary: Dict[str, Any], currency: str
    ) -> str:
        days = int(summary.get("period_days") or 30)
        spent = float(summary.get("total_spent") or 0.0)
        income = float(summary.get("total_income") or 0.0)
        totals = summary.get("category_totals") or {}
        top = ", ".join(
            f"{name.replace('_', ' ')} ({_money(float(v), currency)})"
            for name, v in list(totals.items())[:3]
        )
        text = f"Over the last {days} days you spent {_money(spent, currency)}"
        if top:
            text += f", mostly on {top}"
        text += "."
        if query_type == QueryType.SAVINGS_ADVICE:
            if income > 0:
                text += f" Your net cash flow was {_money(income - spent, currency)}, so a monthly savings target should stay below that surplus."
            recurring = summary.get("recurring") or []
            if recurring:
                text += f" You have {len(recurring)} recurring payments worth reviewing for savings."
            if totals:
                name = next(iter(totals))
                text += f" Trimming {name.replace('_', ' ')} is the quickest lever."
        return text
