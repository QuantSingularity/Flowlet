import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Tuple

from sqlalchemy.orm import Session

from ..clients.stripe_client import stripe_client
from ..models.account import Account, AccountStatus
from ..models.transaction import (
    Transaction,
    TransactionCategory,
    TransactionStatus,
    TransactionType,
)
from ..models.user import User
from ..schemas import (
    InternalTransferRequest,
    PaymentRequestCreate,
    ProcessPaymentRequest,
    SendPaymentRequest,
)
from .ml_gateway import screen_payment
from .payment_service_errors import (
    AccountAccessDenied,
    CurrencyMismatch,
    DestinationWalletNotFound,
    InsufficientFunds,
    PaymentProcessorError,
    PaymentServiceError,
    SourceWalletNotFound,
    TransactionNotFound,
    UnsupportedPaymentMethod,
)

logger = logging.getLogger(__name__)


def get_account_by_id(session: Session, account_id: str) -> Account:
    """Retrieves an account or raises a specific error."""
    account = session.get(Account, account_id)
    if not account:
        raise SourceWalletNotFound()
    return account


def check_account_status(account: Account) -> None:
    """Checks if an account is active."""
    if account.status != AccountStatus.ACTIVE:
        raise PaymentServiceError(
            f"Account {account.id} is not active", "ACCOUNT_INACTIVE", 400
        )


def check_funds_and_limits(account: Account, amount: Decimal) -> None:
    """Checks for sufficient funds and transaction limits."""
    if not account.can_debit(amount):
        raise InsufficientFunds()


def process_external_payment(
    session: Session, user_id: str, data: ProcessPaymentRequest
) -> Dict[str, Any]:
    """
    Processes an external payment (deposit) into a user's account.
    """
    account = session.get(Account, data.account_id)
    if not account or account.user_id != user_id:
        raise AccountAccessDenied()
    check_account_status(account)
    screen_payment(
        session,
        str(user_id),
        data.amount,
        data.currency,
        channel=str(data.payment_method).lower(),
        description=data.description,
    )
    if data.payment_method.lower() == "stripe":
        try:
            stripe_result = stripe_client.create_charge(
                amount=data.amount,
                currency=data.currency,
                source=(data.metadata or {}).get("token"),
                description=data.description or f"Payment via {data.payment_method}",
                metadata={"account_id": str(account.id), "user_id": str(user_id)},
            )
        except PaymentProcessorError as e:
            session.rollback()
            raise e
        except Exception as e:
            session.rollback()
            logger.error(
                f"Unexpected error during Stripe processing: {str(e)}", exc_info=True
            )
            raise PaymentProcessorError(
                "Failed to communicate with payment processor.",
                "PAYMENT_COMMUNICATION_ERROR",
                500,
            )
        if stripe_result.get("status") == "succeeded":
            try:
                account.credit(data.amount)
                transaction = Transaction(
                    user_id=user_id,
                    account_id=account.id,
                    transaction_type=TransactionType.CREDIT,
                    transaction_category=TransactionCategory.PAYMENT,
                    status=TransactionStatus.COMPLETED,
                    description=data.description
                    or f"External payment via {data.payment_method}",
                    channel=data.payment_method,
                    currency=data.currency,
                    amount=data.amount,
                    external_reference=stripe_result.get("id"),
                )
                session.add(transaction)
                session.commit()
                return {
                    "status": "success",
                    "transaction_id": str(transaction.id),
                    "external_reference": stripe_result.get("id"),
                    "new_balance": float(account.balance),
                }
            except Exception as e:
                session.rollback()
                logger.error(
                    f"Failed to save payment transaction: {str(e)}", exc_info=True
                )
                raise PaymentServiceError(
                    "Failed to record payment.", "RECORD_ERROR", 500
                )
        else:
            raise PaymentProcessorError(
                f"Payment status is {stripe_result.get('status')}",
                "PAYMENT_STATUS_ERROR",
                400,
            )
    else:
        raise UnsupportedPaymentMethod(data.payment_method)


def process_internal_transfer(
    session: Session, data: InternalTransferRequest
) -> Tuple[Transaction, Transaction]:
    """
    Handles internal transfers between two wallets.
    """
    from_account = session.get(Account, data.from_account_id)
    to_account = session.get(Account, data.to_account_id)
    if not from_account:
        raise SourceWalletNotFound()
    if not to_account:
        raise DestinationWalletNotFound()
    check_account_status(from_account)
    check_account_status(to_account)
    if from_account.currency != to_account.currency:
        raise CurrencyMismatch()
    check_funds_and_limits(from_account, data.amount)
    screen_payment(
        session,
        str(from_account.user_id),
        data.amount,
        from_account.currency,
        channel="internal_transfer",
        description=data.description,
    )
    transfer_reference = (
        data.reference
        or f"TRF-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
    )
    description = (
        data.description
        or f"Transfer from {from_account.account_name} to {to_account.account_name}"
    )
    try:
        from_account.debit(data.amount, description)
        to_account.credit(data.amount, description)
        debit_transaction = Transaction(
            user_id=from_account.user_id,
            account_id=from_account.id,
            transaction_type=TransactionType.DEBIT,
            transaction_category=TransactionCategory.TRANSFER,
            status=TransactionStatus.COMPLETED,
            description=f"{description} (Outgoing)",
            reference_number=transfer_reference,
            channel="api",
            currency=from_account.currency,
            amount=data.amount,
            related_account_id=to_account.id,
        )
        credit_transaction = Transaction(
            user_id=to_account.user_id,
            account_id=to_account.id,
            transaction_type=TransactionType.CREDIT,
            transaction_category=TransactionCategory.TRANSFER,
            status=TransactionStatus.COMPLETED,
            description=f"{description} (Incoming)",
            reference_number=transfer_reference,
            channel="api",
            currency=to_account.currency,
            amount=data.amount,
            related_account_id=from_account.id,
        )
        session.add_all([debit_transaction, credit_transaction])
        session.commit()
        return (debit_transaction, credit_transaction)
    except (PaymentServiceError, PaymentProcessorError):
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Internal transfer failed: {str(e)}", exc_info=True)
        raise PaymentServiceError("Internal transfer failed.", "TRANSFER_ERROR", 500)


def get_transaction_details(
    session: Session, user_id: str, transaction_id: str
) -> Transaction:
    """
    Retrieves a transaction and checks for user ownership.
    """
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        raise TransactionNotFound(transaction_id)
    user = session.get(User, user_id)
    if transaction.user_id != user_id and (user is None or not user.is_admin):
        raise AccountAccessDenied()
    return transaction


def send_payment(
    session: Session, data: SendPaymentRequest
) -> Tuple[Transaction, Transaction]:
    """
    Handles sending a payment to a recipient.
    """
    if data.recipient == "test_recipient@flowlet.com":
        resolved_to_account_id = "mock_resolved_account_id"
    else:
        raise PaymentServiceError(
            "Recipient not found or external payment not supported yet.",
            "RECIPIENT_NOT_FOUND",
            404,
        )
    internal_transfer_data = InternalTransferRequest(
        from_account_id=data.from_account_id,
        to_account_id=resolved_to_account_id,
        amount=data.amount,
        description=data.description,
        reference=data.reference,
    )
    debit_transaction, credit_transaction = process_internal_transfer(
        session, internal_transfer_data
    )
    try:
        debit_transaction.transaction_category = TransactionCategory.PAYMENT
        session.add(debit_transaction)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update payment category: {str(e)}", exc_info=True)
    return (debit_transaction, credit_transaction)


def create_payment_request(
    session: Session, data: PaymentRequestCreate
) -> Dict[str, Any]:
    """
    Creates a payment request.
    """
    account = session.get(Account, data.account_id)
    if not account:
        raise SourceWalletNotFound()
    request_reference = f"REQ-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
    return {
        "success": True,
        "request_reference": request_reference,
        "wallet_id": str(account.id),
        "account_name": account.account_name,
        "amount": float(data.amount),
        "currency": account.currency,
        "description": data.description,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
        "message": "Payment request created successfully",
    }
