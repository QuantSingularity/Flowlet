import logging
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict

import flask
from flask import Blueprint, g, jsonify, request
from sqlalchemy import select

from ..models.account import Account, AccountType
from ..models.audit_log import AuditEventType, AuditSeverity
from ..models.database import db
from ..models.transaction import (
    Transaction,
    TransactionCategory,
    TransactionStatus,
    TransactionType,
)
from ..security.audit_logger import audit_logger
from .auth import token_required

"\nMulti-Currency and Exchange Rate Routes\n"
multicurrency_bp = Blueprint("multicurrency", __name__, url_prefix="/currency")
logger = logging.getLogger(__name__)


class ExchangeRateManager:
    SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD"]

    @staticmethod
    def get_exchange_rate(from_currency: str, to_currency: str) -> Decimal:
        """Simulate getting a real-time exchange rate."""
        if from_currency == to_currency:
            return Decimal("1.0")
        rates = {
            "USD": {
                "EUR": Decimal("0.92"),
                "GBP": Decimal("0.79"),
                "JPY": Decimal("155.00"),
                "CAD": Decimal("1.37"),
            },
            "EUR": {
                "USD": Decimal("1.08"),
                "GBP": Decimal("0.86"),
                "JPY": Decimal("168.00"),
                "CAD": Decimal("1.49"),
            },
        }
        if from_currency in rates and to_currency in rates[from_currency]:
            return rates[from_currency][to_currency]
        if from_currency != "USD" and to_currency != "USD":
            rate_from_usd = Decimal("1.0") / ExchangeRateManager.get_exchange_rate(
                "USD", from_currency
            )
            rate_to_usd = ExchangeRateManager.get_exchange_rate("USD", to_currency)
            return rate_from_usd * rate_to_usd
        return Decimal("1.0")

    @staticmethod
    def convert_amount(
        amount: Decimal, from_currency: str, to_currency: str
    ) -> Dict[str, Any]:
        """Convert amount between currencies with a simulated fee."""
        rate = ExchangeRateManager.get_exchange_rate(from_currency, to_currency)
        conversion_fee_rate = Decimal("0.005")
        fee_in_from_currency = amount * conversion_fee_rate
        net_amount_to_convert = amount - fee_in_from_currency
        converted_amount = net_amount_to_convert * rate
        converted_amount = converted_amount.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return {
            "original_amount": float(amount),
            "original_currency": from_currency,
            "converted_amount": float(converted_amount),
            "converted_currency": to_currency,
            "exchange_rate": float(rate),
            "conversion_fee": float(
                fee_in_from_currency.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@multicurrency_bp.route("/rate", methods=["GET"])
@token_required
def get_rate() -> "flask.Response":
    """Get the exchange rate between two currencies."""
    try:
        from_currency = request.args.get("from", "USD").upper()
        to_currency = request.args.get("to", "EUR").upper()
        if (
            from_currency not in ExchangeRateManager.SUPPORTED_CURRENCIES
            or to_currency not in ExchangeRateManager.SUPPORTED_CURRENCIES
        ):
            return (
                jsonify(
                    {"error": "Unsupported currency", "code": "UNSUPPORTED_CURRENCY"}
                ),
                400,
            )
        rate = ExchangeRateManager.get_exchange_rate(from_currency, to_currency)
        return (
            jsonify(
                {
                    "success": True,
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "rate": float(rate),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error getting exchange rate: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )


@multicurrency_bp.route("/convert", methods=["POST"])
@token_required
def convert_funds() -> object:
    """Convert funds between two currencies."""
    try:
        data = request.get_json()
        required_fields = ["amount", "from_currency", "to_currency", "from_account_id"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return (
                jsonify(
                    {
                        "error": f"Missing required fields: {', '.join(missing_fields)}",
                        "code": "MISSING_FIELDS",
                    }
                ),
                400,
            )
        amount = Decimal(str(data["amount"]))
        from_currency = data["from_currency"].upper()
        to_currency = data["to_currency"].upper()
        from_account_id = data["from_account_id"]
        if amount <= 0:
            return (
                jsonify({"error": "Amount must be positive", "code": "INVALID_AMOUNT"}),
                400,
            )
        from_account = db.session.get(Account, from_account_id)
        if not from_account or from_account.user_id != g.current_user.id:
            return (
                jsonify(
                    {
                        "error": "Source account not found or access denied",
                        "code": "ACCESS_DENIED",
                    }
                ),
                403,
            )
        if from_account.currency != from_currency:
            return (
                jsonify(
                    {
                        "error": "Currency mismatch for source account",
                        "code": "CURRENCY_MISMATCH",
                    }
                ),
                400,
            )
        if from_account.balance < amount:
            return (
                jsonify(
                    {"error": "Insufficient balance", "code": "INSUFFICIENT_FUNDS"}
                ),
                400,
            )
        conversion_result = ExchangeRateManager.convert_amount(
            amount, from_currency, to_currency
        )
        converted_amount = Decimal(str(conversion_result["converted_amount"]))
        Decimal(str(conversion_result["conversion_fee"]))
        to_account_stmt = select(Account).filter_by(
            user_id=g.current_user.id, currency=to_currency
        )
        to_account = db.session.execute(to_account_stmt).scalar_one_or_none()
        if not to_account:
            to_account = Account(
                user_id=g.current_user.id,
                account_name=f"{to_currency} Exchange Wallet",
                account_type=AccountType.SAVINGS,
                currency=to_currency,
                balance=Decimal("0.00"),
                available_balance=Decimal("0.00"),
            )
            db.session.add(to_account)
            db.session.flush()
        from_account.balance -= amount
        from_account.available_balance -= amount
        to_account.balance += converted_amount
        to_account.available_balance += converted_amount
        db.session.add(
            Transaction(
                account_id=from_account.id,
                user_id=g.current_user.id,
                amount=amount,
                currency=from_currency,
                transaction_type=TransactionType.DEBIT,
                transaction_category=TransactionCategory.TRANSFER,
                status=TransactionStatus.COMPLETED,
                description=f"Currency conversion: {from_currency} to {to_currency}",
                channel="api",
            )
        )
        db.session.add(
            Transaction(
                account_id=to_account.id,
                user_id=g.current_user.id,
                amount=converted_amount,
                currency=to_currency,
                transaction_type=TransactionType.CREDIT,
                transaction_category=TransactionCategory.TRANSFER,
                status=TransactionStatus.COMPLETED,
                description=f"Currency conversion: {from_currency} to {to_currency}",
                channel="api",
            )
        )
        db.session.commit()
        audit_logger.log_event(
            event_type=AuditEventType.FINANCIAL_TRANSACTION,
            description=f"Currency conversion from {from_currency} to {to_currency} for user {g.current_user.id}",
            user_id=g.current_user.id,
            severity=AuditSeverity.MEDIUM,
            resource_type="account",
            resource_id=from_account.id,
        )
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Currency conversion successful",
                    "from_account_id": from_account.id,
                    "to_account_id": to_account.id,
                    "conversion_details": conversion_result,
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error converting funds: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )
