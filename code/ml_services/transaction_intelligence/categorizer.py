import re
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from ..core.logging import get_logger
from .patterns import (
    AMOUNT_RANGES,
    COMPILED_PATTERNS,
    MCC_RANGES,
    SEED_CORPUS,
    SUBCATEGORIES,
)
from .types import TransactionCategory as C
from .types import TransactionInsight

logger = get_logger(__name__)

_CATEGORY_BY_NAME = {category.value: category for category in C}


def _text(tx: Dict[str, Any]) -> str:
    parts = [tx.get("merchant_name"), tx.get("merchant"), tx.get("description")]
    return " ".join(str(part) for part in parts if part).strip()


class AITransactionCategorizer:
    def __init__(self) -> None:
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._classifier: Optional[LogisticRegression] = None
        self._corrections: List[Tuple[str, C]] = []
        self._user_overrides: Dict[str, Dict[str, C]] = defaultdict(dict)
        self._lock = threading.RLock()
        self._fit()

    def _fit(self) -> None:
        corpus = list(SEED_CORPUS) + self._corrections
        texts = [text for text, _ in corpus]
        labels = [category.value for _, category in corpus]
        if len(set(labels)) < 2:
            return
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
        matrix = vectorizer.fit_transform(texts)
        classifier = LogisticRegression(max_iter=1000, C=8.0)
        classifier.fit(matrix, labels)
        self._vectorizer = vectorizer
        self._classifier = classifier

    @staticmethod
    def _normalize_key(text: str) -> str:
        return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()

    def _by_mcc(self, code: Any) -> Optional[C]:
        try:
            value = int(str(code).strip())
        except (TypeError, ValueError):
            return None
        for low, high, category in MCC_RANGES:
            if low <= value <= high:
                return category
        return None

    def _by_patterns(self, text: str) -> Tuple[Optional[C], float]:
        best: Tuple[Optional[C], float] = (None, 0.0)
        for category, patterns in COMPILED_PATTERNS.items():
            hits = sum(1 for pattern in patterns if pattern.search(text))
            if hits:
                score = 0.7 + 0.15 * (hits - 1)
                if score > best[1]:
                    best = (category, score)
        return best

    def _by_model(self, text: str) -> Tuple[Optional[C], float]:
        if not text or self._vectorizer is None or self._classifier is None:
            return None, 0.0
        probabilities = self._classifier.predict_proba(
            self._vectorizer.transform([text])
        )[0]
        index = int(np.argmax(probabilities))
        return _CATEGORY_BY_NAME[self._classifier.classes_[index]], float(
            probabilities[index]
        )

    def categorize_transaction(
        self, transaction_data: Dict[str, Any], user_id: Optional[str] = None
    ) -> TransactionInsight:
        text = _text(transaction_data)
        key = self._normalize_key(text)
        amount = abs(float(transaction_data.get("amount") or 0.0))
        direction = str(
            transaction_data.get("type")
            or transaction_data.get("transaction_type")
            or ""
        ).lower()
        owner = user_id or transaction_data.get("user_id")
        method = "rules"
        category: C = C.OTHER
        confidence = 0.3
        if owner and key in self._user_overrides.get(str(owner), {}):
            category = self._user_overrides[str(owner)][key]
            confidence, method = 0.99, "user_correction"
        else:
            mcc_category = self._by_mcc(
                transaction_data.get("merchant_category_code")
                or transaction_data.get("mcc")
            )
            pattern_category, pattern_score = self._by_patterns(text)
            model_category, model_score = self._by_model(text)
            if pattern_category is not None:
                category, confidence, method = (
                    pattern_category,
                    pattern_score,
                    "pattern",
                )
            if mcc_category is not None and (
                pattern_category is None or mcc_category == pattern_category
            ):
                bonus = 0.1 if pattern_category else 0.0
                if pattern_category is None or confidence < 0.9:
                    category, confidence, method = (
                        mcc_category,
                        min(0.85 + bonus, 0.95),
                        "mcc",
                    )
            if method == "rules" and model_category is not None and model_score >= 0.25:
                category, confidence, method = (
                    model_category,
                    min(model_score * 1.3, 0.8),
                    "model",
                )
            elif method == "pattern" and model_category == category:
                confidence = min(confidence + 0.1, 0.97)
        if (
            category in (C.OTHER, C.TRANSFERS)
            and direction in {"credit", "deposit"}
            and amount > 0
            and re.search(r"salary|payroll|wage", text, re.I)
        ):
            category, confidence, method = C.INCOME, max(confidence, 0.85), "pattern"
        if direction == "refund":
            category, confidence = C.REFUNDS, max(confidence, 0.9)
        insight = TransactionInsight(
            transaction_id=str(
                transaction_data.get("transaction_id")
                or transaction_data.get("id")
                or ""
            ),
            category=category,
            confidence=float(min(max(confidence, 0.0), 1.0)),
            subcategory=self._subcategory(category, text),
            tags=self._tags(transaction_data, category, text, amount),
            anomaly_score=self._anomaly(category, amount),
            method=method,
        )
        insight.insights = self._insights(insight, amount)
        insight.recommendations = self._recommendations(insight)
        return insight

    def categorize_batch(
        self, transactions: Iterable[Dict[str, Any]], user_id: Optional[str] = None
    ) -> List[TransactionInsight]:
        return [self.categorize_transaction(item, user_id) for item in transactions]

    @staticmethod
    def _subcategory(category: C, text: str) -> Optional[str]:
        for name, pattern in SUBCATEGORIES.get(category, {}).items():
            if re.search(pattern, text, re.I):
                return name
        return None

    @staticmethod
    def _tags(tx: Dict[str, Any], category: C, text: str, amount: float) -> List[str]:
        tags: List[str] = []
        if amount >= 1000:
            tags.append("large_purchase")
        if amount and amount < 5:
            tags.append("micro_payment")
        if re.search(r"subscription|monthly|annual|membership", text, re.I):
            tags.append("subscription")
        if re.search(r"online|\.com|web|app", text, re.I):
            tags.append("online")
        country = tx.get("location_country") or tx.get("country_code")
        if country:
            tags.append(f"country_{str(country).lower()}")
        if category in (C.GROCERIES, C.UTILITIES, C.INSURANCE, C.HEALTHCARE):
            tags.append("essential")
        elif category in (C.ENTERTAINMENT, C.RESTAURANTS, C.TRAVEL, C.PERSONAL_CARE):
            tags.append("discretionary")
        return tags

    @staticmethod
    def _anomaly(category: C, amount: float) -> float:
        bounds = AMOUNT_RANGES.get(category)
        if not bounds or amount <= 0:
            return 0.0
        low, high = bounds
        if amount > high:
            return float(min(1.0, 0.5 + np.log10(amount / high)))
        if amount < low * 0.1:
            return 0.3
        return 0.0

    @staticmethod
    def _insights(insight: TransactionInsight, amount: float) -> List[str]:
        notes: List[str] = []
        if insight.anomaly_score >= 0.5:
            notes.append(
                f"Amount is unusually high for {insight.category.value.replace('_', ' ')}"
            )
        if "subscription" in insight.tags:
            notes.append("Looks like a recurring subscription charge")
        if insight.confidence < 0.5:
            notes.append("Category confidence is low; consider confirming it")
        return notes

    @staticmethod
    def _recommendations(insight: TransactionInsight) -> List[str]:
        items: List[str] = []
        if "subscription" in insight.tags:
            items.append("Review whether this subscription is still used")
        if insight.anomaly_score >= 0.5:
            items.append("Verify this transaction is legitimate")
        return items

    def update_user_profile(
        self, user_id: str, transaction_data: Dict[str, Any], corrected_category: str
    ) -> bool:
        category = _CATEGORY_BY_NAME.get(str(corrected_category).lower())
        text = _text(transaction_data)
        if category is None or not text:
            return False
        with self._lock:
            self._user_overrides[str(user_id)][self._normalize_key(text)] = category
            self._corrections.append((text, category))
            if len(self._corrections) % 10 == 0:
                self._fit()
        return True

    def retrain(self) -> None:
        with self._lock:
            self._fit()


def parse_timestamp(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None
