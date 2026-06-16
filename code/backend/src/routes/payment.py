import logging
import uuid
from decimal import Decimal
from typing import Any

import flask
from flask import Blueprint, g, jsonify, request

try:
    from pydantic import ValidationError
except ImportError:

    class ValidationError(Exception):
        pass


from ..models.account import Account
from ..models.audit_log import AuditEventType, AuditSeverity
from ..models.database import db
from ..models.transaction import (
    Transaction,
    TransactionCategory,
    TransactionStatus,
    TransactionType,
)
from ..schemas import ProcessPaymentRequest
from ..security.audit_logger import audit_logger
from ..services.payment_service import get_transaction_details, process_external_payment
from ..services.payment_service_errors import PaymentServiceError
from ..utils.auth import token_required
from ..utils.error_handlers import (
    handle_generic_exception,
    handle_validation_error,
    handle_wallet_service_error,
)

payment_bp = Blueprint("payments", __name__, url_prefix="/payments")
logger = logging.getLogger(__name__)


@payment_bp.route("/process", methods=["POST"])
@token_required
def process_payment() -> "flask.Response":
    """
    Process an external payment (deposit) into a user's account.
    """
    try:
        data = request.get_json()
        payment_request = ProcessPaymentRequest(**data or {})
        user_id = g.current_user.id
        result = process_external_payment(db.session, user_id, payment_request)
        audit_logger.log_event(
            event_type=AuditEventType.TRANSACTION_COMPLETED,
            description=f"External payment of {payment_request.amount} {payment_request.currency} processed via {payment_request.payment_method}",
            user_id=user_id,
            severity=AuditSeverity.MEDIUM,
            details={
                "account_id": payment_request.account_id,
                "amount": float(payment_request.amount),
                "status": result.get("status"),
                "transaction_id": result.get("transaction_id"),
            },
        )
        return (jsonify(result), 200)
    except ValidationError as e:
        return handle_validation_error(e)
    except PaymentServiceError as e:
        db.session.rollback()
        return handle_wallet_service_error(e)
    except Exception as e:
        db.session.rollback()
        return handle_generic_exception(e)


@payment_bp.route("/webhook/<processor_name>", methods=["POST"])
def payment_webhook(processor_name: Any) -> object:
    """
    Webhook endpoint for payment processors to notify of transaction status updates.
    NOTE: This is a placeholder. A real implementation would require a dedicated webhook handler
    that verifies the signature and processes the event.
    """
    try:
        logger.info(
            f"Webhook received from {processor_name}. Payload: {request.get_data(as_text=True)}"
        )
        audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_EVENT,
            description=f"Webhook received from {processor_name}",
            severity=AuditSeverity.LOW,
            details={
                "processor": processor_name,
                "data_length": len(request.get_data()),
            },
        )
        return (jsonify({"status": "received", "processor": processor_name}), 200)
    except Exception as e:
        logger.error(
            f"Payment webhook error for {processor_name}: {str(e)}", exc_info=True
        )
        return handle_generic_exception(e)


@payment_bp.route("/transaction/<transaction_id>", methods=["GET"])
@token_required
def get_transaction_details_route(transaction_id: Any) -> "flask.Response":
    """Get details for a specific transaction"""
    try:
        user_id = g.current_user.id
        transaction = get_transaction_details(db.session, user_id, transaction_id)
        return (jsonify(transaction.to_dict()), 200)
    except PaymentServiceError as e:
        return handle_wallet_service_error(e)
    except Exception as e:
        return handle_generic_exception(e)


@payment_bp.route("/<wallet_id>/send", methods=["POST"])
@token_required
def send_p2p_payment(wallet_id: str) -> None:
    """Send a peer-to-peer payment from a wallet."""
    data = request.get_json() or {}
    recipient_wallet_id = data.get("recipient_wallet_id")
    if not recipient_wallet_id:
        return jsonify({"error": "recipient_wallet_id is required"}), 400

    try:
        amount = Decimal(str(data.get("amount", 0)))
    except Exception:
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    sender = db.session.get(Account, wallet_id)
    if not sender:
        return jsonify({"error": "Sender wallet not found"}), 404
    if sender.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    recipient = db.session.get(Account, recipient_wallet_id)
    if not recipient:
        return jsonify({"error": "Recipient wallet not found"}), 404

    if sender.balance < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    ref = f"P2P-{uuid.uuid4().hex[:12].upper()}"
    desc = data.get("description", "P2P Payment")

    sender.debit(amount)
    recipient.credit(amount)

    debit_txn = Transaction(
        user_id=sender.user_id,
        account_id=sender.id,
        transaction_type=TransactionType.DEBIT,
        transaction_category=TransactionCategory.PAYMENT,
        status=TransactionStatus.COMPLETED,
        amount=amount,
        currency=sender.currency,
        description=f"{desc} (Outgoing)",
        reference_number=ref,
        channel="api",
        related_account_id=recipient.id,
    )
    credit_txn = Transaction(
        user_id=recipient.user_id,
        account_id=recipient.id,
        transaction_type=TransactionType.CREDIT,
        transaction_category=TransactionCategory.PAYMENT,
        status=TransactionStatus.COMPLETED,
        amount=amount,
        currency=recipient.currency,
        description=f"{desc} (Incoming)",
        reference_number=ref,
        channel="api",
        related_account_id=sender.id,
    )
    db.session.add_all([debit_txn, credit_txn])
    db.session.commit()

    return (
        jsonify(
            {
                "transaction_id": debit_txn.id,
                "amount": float(amount),
                "currency": sender.currency,
                "status": "completed",
                "reference": ref,
                "sender_new_balance": float(sender.balance),
            }
        ),
        200,
    )
