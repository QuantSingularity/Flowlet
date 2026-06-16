"""
Card management routes
"""

import hashlib
import random
import string
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import flask
from flask import Blueprint, g, jsonify, request

from ..models.account import Account, AccountStatus
from ..models.card import Card, CardNetwork, CardStatus, CardType
from ..models.database import db
from ..models.transaction import (
    Transaction,
    TransactionCategory,
    TransactionStatus,
    TransactionType,
)
from ..utils.auth import token_required

card_bp = Blueprint("card", __name__, url_prefix="/card")


def _random_digits(n: int) -> str:
    return "".join(random.choices(string.digits, k=n))


def _card_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@card_bp.route("/issue", methods=["POST"])
@token_required
def issue_card() -> object:
    """Issue a new virtual or physical card linked to a wallet."""
    data = request.get_json() or {}
    wallet_id = data.get("wallet_id")
    if not wallet_id:
        return jsonify({"error": "wallet_id is required"}), 400

    account = db.session.get(Account, wallet_id)
    if not account:
        return jsonify({"error": "Wallet not found"}), 404
    if account.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    if account.status != AccountStatus.ACTIVE:
        return jsonify({"error": "Account is not active"}), 400

    card_type_str = data.get("card_type", "virtual").lower()
    try:
        card_type = CardType(card_type_str)
    except ValueError:
        card_type = CardType.VIRTUAL

    spending_limit_raw = data.get("spending_limit", 1000.0)
    try:
        spending_limit = Decimal(str(spending_limit_raw))
    except (InvalidOperation, TypeError):
        spending_limit = Decimal("1000.00")

    last_four = _random_digits(4)
    card_token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    card = Card(
        user_id=g.current_user.id,
        account_id=account.id,
        card_token=card_token,
        card_number_token=str(uuid.uuid4()),
        last_four_digits=last_four,
        card_hash=_card_hash(card_token),
        card_type=card_type,
        card_network=CardNetwork.VISA,
        card_name=f"{g.current_user.first_name} {g.current_user.last_name}",
        status=CardStatus.ACTIVE,
        expiry_month=now.month,
        expiry_year=now.year + 4,
        daily_limit=spending_limit,
        monthly_limit=spending_limit * 10,
        single_transaction_limit=spending_limit,
        is_physical_card=(card_type == CardType.PHYSICAL),
        activated_at=now,
    )
    db.session.add(card)
    db.session.commit()

    return (
        jsonify(
            {
                "card_id": card.id,
                "last_four_digits": card.last_four_digits,
                "card_type": card.card_type.value,
                "card_network": card.card_network.value,
                "status": card.status.value,
                "spending_limit": float(spending_limit),
                "expiry_month": card.expiry_month,
                "expiry_year": card.expiry_year,
                "wallet_id": wallet_id,
            }
        ),
        201,
    )


@card_bp.route("/<card_id>/transaction", methods=["POST"])
@token_required
def card_transaction(card_id: str) -> object:
    """Process a card transaction (purchase)."""
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": "Card not found"}), 404
    if card.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    if card.status != CardStatus.ACTIVE:
        return jsonify({"error": "Card is not active"}), 400

    data = request.get_json() or {}
    try:
        amount = Decimal(str(data.get("amount", 0)))
    except (InvalidOperation, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    account = db.session.get(Account, card.account_id)
    if not account or account.status != AccountStatus.ACTIVE:
        return jsonify({"error": "Associated account is not active"}), 400

    if account.balance < amount:
        return jsonify({"error": "Insufficient funds", "status": "declined"}), 400

    if amount > card.single_transaction_limit:
        return (
            jsonify({"error": "Exceeds transaction limit", "status": "declined"}),
            400,
        )

    # Debit the account
    account.debit(amount)
    card.last_used_at = datetime.now(timezone.utc)
    card.total_spent_today = (card.total_spent_today or Decimal("0")) + amount
    card.total_spent_month = (card.total_spent_month or Decimal("0")) + amount

    txn = Transaction(
        user_id=g.current_user.id,
        account_id=account.id,
        card_id=card.id,
        transaction_type=TransactionType.DEBIT,
        transaction_category=TransactionCategory.PURCHASE,
        status=TransactionStatus.COMPLETED,
        amount=amount,
        currency=account.currency,
        description=data.get(
            "description", f"Card purchase at {data.get('merchant', 'unknown')}"
        ),
        channel="card",
    )
    db.session.add(txn)
    db.session.commit()

    return (
        jsonify(
            {
                "transaction_id": txn.id,
                "amount": float(amount),
                "currency": account.currency,
                "status": "approved",
                "merchant": data.get("merchant", ""),
                "new_balance": float(account.balance),
            }
        ),
        200,
    )


@card_bp.route("/<card_id>/freeze", methods=["POST"])
@token_required
def freeze_card(card_id: str) -> None:
    """Freeze a card."""
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": "Card not found"}), 404
    if card.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    card.status = CardStatus.BLOCKED
    card.blocked_at = datetime.now(timezone.utc)
    card.blocked_reason = "User requested freeze"
    db.session.commit()
    return jsonify({"card_id": card.id, "status": card.status.value}), 200


@card_bp.route("/<card_id>/unfreeze", methods=["POST"])
@token_required
def unfreeze_card(card_id: str) -> object:
    """Unfreeze a card."""
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": "Card not found"}), 404
    if card.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    card.status = CardStatus.ACTIVE
    card.blocked_at = None
    card.blocked_reason = None
    db.session.commit()
    return jsonify({"card_id": card.id, "status": card.status.value}), 200


@card_bp.route("/<card_id>/controls", methods=["PUT", "PATCH"])
@token_required
def update_card_controls(card_id: str) -> None:
    """Update card spending controls."""
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": "Card not found"}), 404
    if card.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}
    if "daily_limit" in data:
        card.daily_limit = Decimal(str(data["daily_limit"]))
    if "monthly_limit" in data:
        card.monthly_limit = Decimal(str(data["monthly_limit"]))
    if "single_transaction_limit" in data:
        card.single_transaction_limit = Decimal(str(data["single_transaction_limit"]))
    if "is_online_enabled" in data:
        card.is_online_enabled = bool(data["is_online_enabled"])
    if "is_international_enabled" in data:
        card.is_international_enabled = bool(data["is_international_enabled"])
    if "is_contactless_enabled" in data:
        card.is_contactless_enabled = bool(data["is_contactless_enabled"])

    db.session.commit()
    return jsonify({"card_id": card.id, "status": "controls_updated"}), 200


@card_bp.route("/", methods=["GET"])
@token_required
def list_cards() -> "flask.Response":
    """List all cards for the current user."""
    cards = db.session.query(Card).filter(Card.user_id == g.current_user.id).all()
    return (
        jsonify(
            {
                "cards": [
                    {
                        "card_id": c.id,
                        "last_four": c.last_four_digits,
                        "status": c.status.value,
                        "card_type": c.card_type.value,
                    }
                    for c in cards
                ]
            }
        ),
        200,
    )


@card_bp.route("/<card_id>", methods=["GET"])
@token_required
def get_card(card_id: str) -> "flask.Response":
    """Get card details."""
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": "Card not found"}), 404
    if card.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    return (
        jsonify(
            {
                "card_id": card.id,
                "last_four_digits": card.last_four_digits,
                "card_type": card.card_type.value,
                "status": card.status.value,
                "expiry_month": card.expiry_month,
                "expiry_year": card.expiry_year,
                "daily_limit": float(card.daily_limit),
                "monthly_limit": float(card.monthly_limit),
            }
        ),
        200,
    )
