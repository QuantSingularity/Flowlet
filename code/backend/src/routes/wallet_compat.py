"""
Wallet compatibility routes – expose /wallet/* endpoints expected by tests and clients.
All logic delegates to existing wallet_service and account models.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

import flask
from flask import Blueprint, g, jsonify, request

from ..models.account import Account
from ..models.database import db
from ..models.transaction import Transaction
from ..schemas.wallet_schemas import (
    CreateWalletRequest,
    DepositFundsRequest,
    WithdrawFundsRequest,
)
from ..services.wallet_service import (
    InsufficientFunds,
    WalletServiceError,
    create_wallet,
    process_deposit,
    process_withdrawal,
)
from ..utils.auth import token_required

wallet_compat_bp = Blueprint("wallet_compat", __name__, url_prefix="/wallet")
logger = logging.getLogger(__name__)


def _parse_amount(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid amount: {value}")


@wallet_compat_bp.route("/create", methods=["POST"])
@token_required
def create_wallet_endpoint() -> "flask.Response":
    """Create a new wallet for the authenticated user."""
    data = request.get_json() or {}
    currency = data.get("currency", "USD").upper()
    initial_balance_raw = data.get("initial_balance", 0)
    try:
        initial_balance = _parse_amount(initial_balance_raw)
    except ValueError:
        return jsonify({"error": "Invalid initial_balance"}), 400

    req = CreateWalletRequest(
        account_name=data.get("account_name", f"{currency} Wallet"),
        account_type=data.get("account_type", "checking"),
        currency=currency,
        initial_balance=initial_balance,
    )
    try:
        account = create_wallet(db.session, g.current_user.id, req)
    except WalletServiceError as e:
        return jsonify({"error": e.message, "code": e.error_code}), e.status_code
    except Exception as e:
        logger.error(f"Wallet creation error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    return (
        jsonify(
            {
                "wallet_id": account.id,
                "account_id": account.id,
                "currency": account.currency,
                "balance": float(account.balance),
                "status": account.status.value,
                "account_type": account.account_type.value,
            }
        ),
        201,
    )


@wallet_compat_bp.route("/<wallet_id>/balance", methods=["GET"])
@token_required
def get_wallet_balance(wallet_id: str) -> "flask.Response":
    """Get balance for a wallet."""
    account = db.session.get(Account, wallet_id)
    if not account:
        return jsonify({"error": "Wallet not found"}), 404
    if account.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    return (
        jsonify(
            {
                "wallet_id": account.id,
                "balance": float(account.balance),
                "available_balance": float(account.available_balance),
                "currency": account.currency,
            }
        ),
        200,
    )


@wallet_compat_bp.route("/<wallet_id>/deposit", methods=["POST"])
@token_required
def wallet_deposit(wallet_id: str) -> object:
    """Deposit funds into a wallet."""
    account = db.session.get(Account, wallet_id)
    if not account:
        return jsonify({"error": "Wallet not found"}), 404
    if account.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}
    try:
        amount = _parse_amount(data.get("amount", 0))
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400

    req = DepositFundsRequest(amount=amount, description=data.get("description"))
    try:
        transaction = process_deposit(db.session, wallet_id, req)
    except WalletServiceError as e:
        db.session.rollback()
        return jsonify({"error": e.message, "code": e.error_code}), e.status_code
    except Exception as e:
        db.session.rollback()
        logger.error(f"Deposit error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    db.session.refresh(account)
    return (
        jsonify(
            {
                "transaction_id": transaction.id,
                "new_balance": float(account.balance),
                "amount": float(amount),
                "currency": account.currency,
            }
        ),
        200,
    )


@wallet_compat_bp.route("/<wallet_id>/withdraw", methods=["POST"])
@token_required
def wallet_withdraw(wallet_id: str) -> object:
    """Withdraw funds from a wallet."""
    account = db.session.get(Account, wallet_id)
    if not account:
        return jsonify({"error": "Wallet not found"}), 404
    if account.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}
    try:
        amount = _parse_amount(data.get("amount", 0))
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400

    if account.balance < amount:
        return (
            jsonify({"error": "Insufficient funds", "code": "INSUFFICIENT_FUNDS"}),
            400,
        )

    req = WithdrawFundsRequest(amount=amount, description=data.get("description"))
    try:
        transaction = process_withdrawal(db.session, wallet_id, req)
    except InsufficientFunds:
        db.session.rollback()
        return (
            jsonify({"error": "Insufficient funds", "code": "INSUFFICIENT_FUNDS"}),
            400,
        )
    except WalletServiceError as e:
        db.session.rollback()
        return jsonify({"error": e.message, "code": e.error_code}), e.status_code
    except Exception as e:
        db.session.rollback()
        logger.error(f"Withdrawal error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    db.session.refresh(account)
    return (
        jsonify(
            {
                "transaction_id": transaction.id,
                "new_balance": float(account.balance),
                "amount": float(amount),
                "currency": account.currency,
            }
        ),
        200,
    )


@wallet_compat_bp.route("/<wallet_id>/transactions", methods=["GET"])
@token_required
def wallet_transactions(wallet_id: str) -> object:
    """Get transaction history for a wallet."""
    account = db.session.get(Account, wallet_id)
    if not account:
        return jsonify({"error": "Wallet not found"}), 404
    if account.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    limit = min(int(request.args.get("limit", 20)), 100)
    txns = (
        db.session.query(Transaction)
        .filter(Transaction.account_id == wallet_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )
    return (
        jsonify({"transactions": [t.to_dict() for t in txns], "wallet_id": wallet_id}),
        200,
    )
