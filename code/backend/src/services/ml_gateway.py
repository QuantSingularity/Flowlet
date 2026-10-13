import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from ..models.account import Account
from ..models.fraud_alert import FraudAlert, FraudAlertStatus
from ..models.transaction import Transaction, TransactionStatus, TransactionType
from ..models.user import User
from .payment_service_errors import FraudBlocked

logger = logging.getLogger(__name__)

try:
    from ml_services.config import get_settings
    from ml_services.core.enums import FraudAction
    from ml_services.core.exceptions import InvalidTransactionError
    from ml_services.fraud_detection.types import FraudAlert as MLAlert
    from ml_services.serving import get_container

    ML_AVAILABLE = True
except Exception as exc:
    logger.error("ml_services is unavailable: %s", exc)
    ML_AVAILABLE = False

OUTFLOW_TYPES = (
    TransactionType.DEBIT,
    TransactionType.PAYMENT,
    TransactionType.TRANSFER,
)
ACTIVE_STATUSES = (
    TransactionStatus.COMPLETED,
    TransactionStatus.PENDING,
    TransactionStatus.PROCESSING,
)
_HIGH_RISK_PATTERNS = (
    (re.compile(r"casino|gambl|betting|\bbet\b|poker|lotto", re.I), "gambling"),
    (
        re.compile(r"bitcoin|crypto|binance|coinbase|\bbtc\b|\beth\b", re.I),
        "cryptocurrency",
    ),
    (
        re.compile(r"western union|moneygram|wire transfer|remittance", re.I),
        "wire_transfer",
    ),
    (re.compile(r"cash advance", re.I), "cash_advance"),
    (re.compile(r"adult|escort", re.I), "adult_entertainment"),
)


def ml_enabled() -> bool:
    return ML_AVAILABLE and get_settings().enabled


def get_ml():
    if not ML_AVAILABLE:
        return None
    return get_container()


def warm_up_models() -> None:
    if not ml_enabled():
        return
    try:
        get_container().warm_up(block=False)
    except Exception as exc:
        logger.error("ML warm up failed to start: %s", exc)


def _merchant_category(transaction: Transaction) -> Optional[str]:
    haystack = " ".join(
        part for part in (transaction.merchant_name, transaction.description) if part
    )
    for pattern, category in _HIGH_RISK_PATTERNS:
        if pattern.search(haystack):
            return category
    return None


def load_user_history(
    session: Any, user_id: str, days: int = 90, limit: int = 500
) -> List[Dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    statement = (
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.created_at >= cutoff,
            Transaction.transaction_type.in_(OUTFLOW_TYPES),
            Transaction.status.in_(ACTIVE_STATUSES),
        )
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    rows = session.execute(statement).scalars().all()
    history: List[Dict[str, Any]] = []
    for row in rows:
        created = row.created_at
        if created is None:
            continue
        history.append(
            {
                "timestamp": created,
                "amount": float(row.amount),
                "merchant_category": _merchant_category(row),
                "device_fingerprint": row.device_fingerprint,
                "location_country": (row.country_code or "").upper() or None,
                "currency": row.currency,
                "transaction_id": row.transaction_id,
            }
        )
    history.reverse()
    return history


def _score_payload(
    user_id: str,
    amount: Any,
    currency: str,
    transaction_id: Optional[str],
    channel: Optional[str],
    merchant_category: Optional[str],
    location_country: Optional[str],
    device_fingerprint: Optional[str],
    ip_address: Optional[str],
    description: Optional[str],
) -> Dict[str, Any]:
    category = merchant_category
    if category is None and description:
        for pattern, name in _HIGH_RISK_PATTERNS:
            if pattern.search(description):
                category = name
                break
    return {
        "transaction_id": transaction_id,
        "user_id": str(user_id),
        "amount": str(Decimal(str(amount))),
        "currency": currency,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channel": channel,
        "merchant_category": category,
        "location_country": location_country,
        "device_fingerprint": device_fingerprint,
        "ip_address": ip_address,
    }


def score_transaction(
    session: Any,
    user_id: str,
    amount: Any,
    currency: str = "USD",
    transaction_id: Optional[str] = None,
    channel: Optional[str] = None,
    merchant_category: Optional[str] = None,
    location_country: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
    ip_address: Optional[str] = None,
    description: Optional[str] = None,
    use_database_history: bool = True,
) -> Optional["MLAlert"]:
    if not ml_enabled():
        return None
    payload = _score_payload(
        user_id,
        amount,
        currency,
        transaction_id,
        channel,
        merchant_category,
        location_country,
        device_fingerprint,
        ip_address,
        description,
    )
    history = None
    if use_database_history:
        try:
            history = load_user_history(session, str(user_id))
        except Exception as exc:
            logger.warning("History lookup failed, scoring without it: %s", exc)
    service = get_container().fraud
    return service.detect(payload, history, record=True)


def persist_alert(
    session: Any, alert: "MLAlert", commit: bool = False
) -> Optional[FraudAlert]:
    try:
        kind = alert.fraud_types[0].value if alert.fraud_types else "model_flag"
        record = FraudAlert(
            user_id=alert.user_id if alert.user_id != "anonymous" else None,
            transaction_id=str(alert.transaction_id)[:64],
            alert_type=kind,
            status=FraudAlertStatus.PENDING,
            description=alert.explanation.get("summary"),
            risk_score=round(alert.risk_score * 100.0, 2),
            risk_level=alert.risk_level.value,
            action=alert.action.value,
            model_version=str(alert.model_version)[:64],
            ml_alert_id=alert.alert_id,
        )
        record.set_details(
            {
                "fraud_types": [t.value for t in alert.fraud_types],
                "recommended_actions": alert.recommended_actions,
                "rule_hits": alert.explanation.get("rule_hits", []),
                "primary_risk_factors": alert.explanation.get(
                    "primary_risk_factors", []
                ),
                "confidence": alert.confidence,
            }
        )
        session.add(record)
        if commit:
            session.commit()
        return record
    except Exception as exc:
        logger.error("Failed to persist fraud alert: %s", exc)
        try:
            session.rollback()
        except Exception:
            pass
        return None


def screen_payment(
    session: Any,
    user_id: str,
    amount: Any,
    currency: str = "USD",
    channel: str = "api",
    description: Optional[str] = None,
    transaction_id: Optional[str] = None,
    location_country: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Optional["MLAlert"]:
    if not ml_enabled():
        return None
    settings = get_settings()
    if not settings.enforce_in_payments:
        return None
    try:
        alert = score_transaction(
            session,
            user_id,
            amount,
            currency,
            transaction_id=transaction_id,
            channel=channel,
            location_country=location_country,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            description=description,
        )
    except InvalidTransactionError:
        raise
    except Exception as exc:
        logger.error("Fraud screening failed: %s", exc)
        if settings.fail_open:
            return None
        raise FraudBlocked("Fraud screening is temporarily unavailable")
    if alert is None:
        return None
    if alert.action == FraudAction.BLOCK and settings.block_in_payments:
        persist_alert(session, alert, commit=True)
        raise FraudBlocked()
    if alert.is_flagged:
        persist_alert(session, alert, commit=False)
    return alert


def build_risk_user_data(session: Any, user: User) -> Dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=180)
    statement = (
        select(Transaction)
        .where(Transaction.user_id == user.id, Transaction.created_at >= cutoff)
        .order_by(Transaction.created_at.desc())
        .limit(1000)
    )
    rows = session.execute(statement).scalars().all()
    history = [
        {
            "timestamp": row.created_at,
            "amount": float(row.amount),
            "type": row.transaction_type.value if row.transaction_type else None,
            "status": row.status.value if row.status else None,
            "merchant_category": _merchant_category(row),
            "device_fingerprint": row.device_fingerprint,
            "location_country": (row.country_code or "").upper() or None,
        }
        for row in rows
        if row.created_at is not None
    ]
    accounts = (
        session.execute(select(Account).where(Account.user_id == user.id))
        .scalars()
        .all()
    )
    available = sum(float(a.available_balance or a.balance or 0) for a in accounts)
    alerts = (
        session.execute(
            select(FraudAlert)
            .where(FraudAlert.user_id == user.id, FraudAlert.created_at >= cutoff)
            .limit(200)
        )
        .scalars()
        .all()
    )
    created = getattr(user, "created_at", None)
    age_days = None
    if created is not None:
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_days = max((datetime.now(timezone.utc) - created).days, 0)
    kyc = (
        user.kyc_status.value
        if hasattr(user.kyc_status, "value")
        else str(user.kyc_status)
    )
    return {
        "account_age_days": age_days,
        "kyc_status": kyc,
        "transaction_history": history,
        "account_balances": {"available": available, "total": available},
        "fraud_alert_scores": [float(a.risk_score or 0.0) / 100.0 for a in alerts],
        "security_incidents": [
            a.id for a in alerts if a.status == FraudAlertStatus.CONFIRMED
        ],
    }


def build_chat_context(session: Any, user: User) -> Dict[str, Any]:
    accounts = (
        session.execute(select(Account).where(Account.user_id == user.id))
        .scalars()
        .all()
    )
    balances: Dict[str, float] = {}
    for account in accounts:
        balances[account.currency] = balances.get(account.currency, 0.0) + float(
            account.available_balance or account.balance or 0
        )
    statement = (
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(200)
    )
    rows = session.execute(statement).scalars().all()
    records = [
        {
            "transaction_id": row.transaction_id,
            "description": row.description,
            "merchant_name": row.merchant_name,
            "amount": float(row.amount),
            "currency": row.currency,
            "type": row.transaction_type.value if row.transaction_type else None,
            "timestamp": row.created_at,
            "merchant_category_code": row.merchant_category_code,
        }
        for row in rows
    ]
    context: Dict[str, Any] = {
        "balances": balances,
        "currency": next(iter(balances), "USD"),
        "recent_transactions": records[:5],
    }
    if records:
        container = get_ml()
        analysis = container.spending.analyze_spending_patterns(
            str(user.id), records, 30
        )
        context["spending_summary"] = analysis.to_dict()
    return context
