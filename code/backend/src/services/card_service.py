import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from src.models.account import Account, AccountStatus
from src.models.card import Card, CardStatus, CardType
from src.models.database import db
from src.models.user import User
from src.security.audit_logger import AuditLogger
from src.security.input_validator import InputValidator
from src.utils.luhn import validate_luhn

logger = logging.getLogger(__name__)
audit_logger = AuditLogger()
input_validator = InputValidator()


class CardServiceError(Exception):
    """Custom exception for CardService errors."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


class CardService:
    """
    A secure and consolidated service layer for all card management operations.
    Encapsulates business logic, security checks, and database interactions.
    """

    MAX_CARDS_PER_ACCOUNT = 5
    PIN_ATTEMPTS_LIMIT = 3
    PIN_LOCK_DURATION_MINUTES = 30

    def _generate_card_number(self, card_type: CardType) -> str:
        """Generates a mock 16-digit card number with a valid Luhn checksum."""
        if card_type in [CardType.DEBIT, CardType.CREDIT]:
            prefix = "4" if secrets.randbelow(2) == 0 else "5"
        else:
            prefix = "6"
        digits = prefix + "".join((str(secrets.randbelow(10)) for _ in range(14)))
        total = 0
        for i, digit in enumerate(digits):
            n = int(digit)
            if i % 2 == 0:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        checksum = (10 - total % 10) % 10
        return digits + str(checksum)

    def _generate_cvv(self) -> str:
        """Generates a mock 3-digit CVV."""
        return "".join((str(secrets.randbelow(10)) for _ in range(3)))

    def _validate_card_input(self, data: Dict[str, Any]) -> object:
        """Validates input data for card issuance."""
        required_fields = ["account_id", "card_type"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise CardServiceError(
                f"Missing required fields: {', '.join(missing_fields)}",
                "MISSING_FIELDS",
            )
        try:
            card_type = CardType(data["card_type"].lower())
        except ValueError:
            raise CardServiceError(
                f"Invalid card type. Must be one of: {[t.value for t in CardType]}",
                "INVALID_CARD_TYPE",
            )
        spending_limits = data.get("spending_limits", {})
        daily_limit = Decimal(str(spending_limits.get("daily", "1000.00")))
        monthly_limit = Decimal(str(spending_limits.get("monthly", "10000.00")))
        per_transaction_limit = Decimal(
            str(spending_limits.get("per_transaction", "500.00"))
        )
        if daily_limit <= 0 or monthly_limit <= 0 or per_transaction_limit <= 0:
            raise CardServiceError("Spending limits must be positive", "INVALID_LIMITS")
        if daily_limit > monthly_limit:
            raise CardServiceError(
                "Daily limit cannot exceed monthly limit", "INVALID_LIMIT_RELATIONSHIP"
            )
        return (card_type, daily_limit, monthly_limit, per_transaction_limit)

    def issue_card(
        self, user: User, data: Dict[str, Any], ip_address: str
    ) -> Tuple[Card, str, str]:
        """
        Issues a new virtual or physical card, handling all security and validation.

        Returns:
            Tuple[Card, str, str]: The new Card object, the raw card number, and the raw CVV.
        """
        try:
            card_type, daily_limit, monthly_limit, per_transaction_limit = (
                self._validate_card_input(data)
            )
            account = Account.query.get(data["account_id"])
            if not account:
                raise CardServiceError("Account not found", "ACCOUNT_NOT_FOUND")
            if account.user_id != user.id and (not user.is_admin):
                raise CardServiceError("Access denied", "ACCESS_DENIED")
            if account.status != AccountStatus.ACTIVE:
                raise CardServiceError(
                    "Account must be active to issue cards", "ACCOUNT_INACTIVE"
                )
            existing_cards = (
                Card.query.filter_by(account_id=account.id)
                .filter(Card.status.in_([CardStatus.ACTIVE, CardStatus.BLOCKED]))
                .count()
            )
            if existing_cards >= self.MAX_CARDS_PER_ACCOUNT:
                raise CardServiceError(
                    f"Maximum {self.MAX_CARDS_PER_ACCOUNT} cards allowed per account",
                    "CARD_LIMIT_EXCEEDED",
                )
            card_number = self._generate_card_number(card_type)
            cvv = self._generate_cvv()
            if not validate_luhn(card_number):
                raise CardServiceError(
                    "Generated card number failed Luhn check", "LUHN_CHECK_FAILED"
                )
            expiry_date = datetime.now(timezone.utc) + timedelta(days=1095)
            controls = data.get("controls", {})
            blocked_merchant_categories = json.dumps(
                controls.get("blocked_merchant_categories", [])
            )
            initial_status = (
                CardStatus.ACTIVE
                if card_type == CardType.VIRTUAL
                else CardStatus.PENDING_ACTIVATION
            )
            card = Card(
                user_id=user.id,
                account_id=account.id,
                card_type=card_type,
                card_network=self._determine_card_network(card_number),
                card_name=input_validator.sanitize_string(
                    data.get("card_name", f"{card_type.value.title()} Card")
                ),
                status=initial_status,
                expiry_month=expiry_date.month,
                expiry_year=expiry_date.year,
                daily_limit=daily_limit,
                monthly_limit=monthly_limit,
                single_transaction_limit=per_transaction_limit,
                is_online_enabled=controls.get("online_transactions", True),
                is_contactless_enabled=controls.get("contactless_payments", True),
                is_international_enabled=controls.get(
                    "international_transactions", False
                ),
                blocked_merchant_categories=blocked_merchant_categories,
                is_physical_card=card_type != CardType.VIRTUAL,
            )
            card.set_card_number(card_number)
            card.set_cvv(cvv)
            db.session.add(card)
            db.session.commit()
            audit_logger.log_user_event(
                user_id=user.id,
                event_type="card_issued",
                details={
                    "card_id": str(card.id),
                    "card_type": card_type.value,
                    "account_id": str(account.id),
                    "ip": ip_address,
                },
            )
            return (card, card_number, cvv)
        except CardServiceError as e:
            db.session.rollback()
            logger.error(f"Card issuance error: {e.code} - {e.message}")
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected card issuance error: {str(e)}")
            raise CardServiceError("Failed to issue card", "CARD_ISSUANCE_ERROR")

    def get_card_details(self, user: User, card_id: str) -> Card:
        """Retrieves a card, performing access control."""
        card = Card.query.get(card_id)
        if not card:
            raise CardServiceError("Card not found", "CARD_NOT_FOUND")
        if card.user_id != user.id and (not user.is_admin):
            audit_logger.log_security_event(
                event_type="unauthorized_card_access",
                details={"user_id": user.id, "card_id": card_id},
            )
            raise CardServiceError("Access denied", "ACCESS_DENIED")
        return card

    def activate_card(
        self, user: User, card_id: str, pin: str, activation_code: Optional[str] = None
    ) -> Card:
        """Activates a card, setting the PIN and validating the activation code."""
        card = self.get_card_details(user, card_id)
        if card.status != CardStatus.PENDING_ACTIVATION:
            raise CardServiceError(
                "Card is not in pending activation status", "INVALID_CARD_STATUS"
            )
        if card.is_physical_card:
            if not activation_code:
                raise CardServiceError(
                    "Activation code is required for physical cards",
                    "ACTIVATION_CODE_REQUIRED",
                )
            if not input_validator.validate_activation_code(activation_code):
                raise CardServiceError(
                    "Invalid activation code format", "INVALID_ACTIVATION_CODE"
                )
        if not input_validator.validate_pin(pin):
            raise CardServiceError("PIN must be exactly 4 digits", "INVALID_PIN_FORMAT")
        card.set_pin(pin)
        card.status = CardStatus.ACTIVE
        card.activated_at = datetime.now(timezone.utc)
        card.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        audit_logger.log_user_event(
            user_id=user.id, event_type="card_activated", details={"card_id": card_id}
        )
        return card

    def update_pin(
        self, user: User, card_id: str, current_pin: str, new_pin: str
    ) -> Card:
        """Updates the card PIN after verifying the current PIN."""
        card = self.get_card_details(user, card_id)
        if card.status != CardStatus.ACTIVE:
            raise CardServiceError(
                "Card must be active to update PIN", "CARD_NOT_ACTIVE"
            )
        if card.is_pin_locked():
            raise CardServiceError(
                "PIN is locked due to too many failed attempts", "PIN_LOCKED"
            )
        if not input_validator.validate_pin(new_pin):
            raise CardServiceError(
                "New PIN must be exactly 4 digits", "INVALID_PIN_FORMAT"
            )
        is_valid, message = card.verify_pin(current_pin)
        if not is_valid:
            db.session.commit()
            audit_logger.log_security_event(
                event_type="pin_verification_failed",
                details={"card_id": card_id, "user_id": user.id},
            )
            raise CardServiceError(message, "INVALID_CURRENT_PIN")
        card.set_pin(new_pin)
        card.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        audit_logger.log_user_event(
            user_id=user.id, event_type="card_pin_changed", details={"card_id": card_id}
        )
        return card

    def _determine_card_network(self, card_number: str) -> str:
        """Determines the card network based on the card number prefix."""
        if card_number.startswith("4"):
            return "visa"
        elif card_number.startswith("5"):
            return "mastercard"
        elif card_number.startswith("34") or card_number.startswith("37"):
            return "amex"
        elif card_number.startswith("6"):
            return "discover"
        return "unknown"

    def freeze_card(
        self, user: User, card_id: str, reason: str, ip_address: str
    ) -> Card:
        """Freezes/blocks a card."""
        card = self.get_card_details(user, card_id)
        if card.status not in [CardStatus.ACTIVE]:
            raise CardServiceError(
                "Only active cards can be frozen", "INVALID_CARD_STATUS"
            )
        card.status = CardStatus.BLOCKED
        card.blocked_reason = reason
        card.blocked_at = datetime.now(timezone.utc)
        card.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        audit_logger.log_user_event(
            user_id=user.id,
            event_type="card_frozen",
            details={"card_id": card_id, "reason": reason, "ip": ip_address},
        )
        return card

    def unfreeze_card(self, user: User, card_id: str, ip_address: str) -> Card:
        """Unfreezes/unblocks a card."""
        card = self.get_card_details(user, card_id)
        if card.status != CardStatus.BLOCKED:
            raise CardServiceError("Card is not currently frozen", "CARD_NOT_FROZEN")
        if card.is_expired():
            raise CardServiceError("Cannot unfreeze an expired card", "CARD_EXPIRED")
        card.status = CardStatus.ACTIVE
        card.blocked_reason = None
        card.blocked_at = None
        card.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        audit_logger.log_user_event(
            user_id=user.id,
            event_type="card_unfrozen",
            details={"card_id": card_id, "ip": ip_address},
        )
        return card

    def cancel_card(
        self, user: User, card_id: str, reason: str, ip_address: str
    ) -> Card:
        """Cancels a card permanently."""
        card = self.get_card_details(user, card_id)
        if card.status == CardStatus.CANCELLED:
            raise CardServiceError(
                "Card is already cancelled", "CARD_ALREADY_CANCELLED"
            )
        card.status = CardStatus.CANCELLED
        card.cancelled_reason = reason
        card.cancelled_at = datetime.now(timezone.utc)
        card.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        audit_logger.log_user_event(
            user_id=user.id,
            event_type="card_cancelled",
            details={"card_id": card_id, "reason": reason, "ip": ip_address},
        )
        return card

    def update_spending_limits(
        self, user: User, card_id: str, data: Dict[str, Any]
    ) -> Tuple[Card, Dict[str, Any]]:
        """Updates card spending limits."""
        card = self.get_card_details(user, card_id)
        if card.status not in [CardStatus.ACTIVE, CardStatus.BLOCKED]:
            raise CardServiceError(
                "Cannot update limits for cancelled or expired cards",
                "INVALID_CARD_STATUS",
            )
        changes = {}
        if "daily_limit" in data:
            try:
                new_limit = Decimal(str(data["daily_limit"]))
                if new_limit <= 0:
                    raise CardServiceError(
                        "Daily limit must be positive", "INVALID_DAILY_LIMIT"
                    )
                old_limit = card.daily_limit
                card.daily_limit = new_limit
                changes["daily_limit"] = {
                    "old": float(old_limit),
                    "new": float(new_limit),
                }
            except (ValueError, TypeError):
                raise CardServiceError(
                    "Invalid daily limit format", "INVALID_DAILY_LIMIT_FORMAT"
                )
        if "monthly_limit" in data:
            try:
                new_limit = Decimal(str(data["monthly_limit"]))
                if new_limit <= 0:
                    raise CardServiceError(
                        "Monthly limit must be positive", "INVALID_MONTHLY_LIMIT"
                    )
                old_limit = card.monthly_limit
                card.monthly_limit = new_limit
                changes["monthly_limit"] = {
                    "old": float(old_limit),
                    "new": float(new_limit),
                }
            except (ValueError, TypeError):
                raise CardServiceError(
                    "Invalid monthly limit format", "INVALID_MONTHLY_LIMIT_FORMAT"
                )
        if "per_transaction_limit" in data:
            try:
                new_limit = Decimal(str(data["per_transaction_limit"]))
                if new_limit <= 0:
                    raise CardServiceError(
                        "Per-transaction limit must be positive",
                        "INVALID_TRANSACTION_LIMIT",
                    )
                old_limit = card.single_transaction_limit
                card.single_transaction_limit = new_limit
                changes["per_transaction_limit"] = {
                    "old": float(old_limit),
                    "new": float(new_limit),
                }
            except (ValueError, TypeError):
                raise CardServiceError(
                    "Invalid per-transaction limit format",
                    "INVALID_TRANSACTION_LIMIT_FORMAT",
                )
        if card.daily_limit > card.monthly_limit:
            raise CardServiceError(
                "Daily limit cannot exceed monthly limit", "INVALID_LIMIT_RELATIONSHIP"
            )
        card.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return (card, changes)

    def update_card_controls(
        self, user: User, card_id: str, data: Dict[str, Any]
    ) -> Tuple[Card, Dict[str, Any]]:
        """Updates card controls (online, contactless, international, merchant categories)."""
        card = self.get_card_details(user, card_id)
        if card.status not in [CardStatus.ACTIVE, CardStatus.BLOCKED]:
            raise CardServiceError(
                "Cannot update controls for cancelled or expired cards",
                "INVALID_CARD_STATUS",
            )
        changes = {}
        if "online_transactions" in data:
            old_value = card.is_online_enabled
            card.is_online_enabled = bool(data["online_transactions"])
            if old_value != card.is_online_enabled:
                changes["online_transactions"] = {
                    "old": old_value,
                    "new": card.is_online_enabled,
                }
        if "contactless_payments" in data:
            old_value = card.is_contactless_enabled
            card.is_contactless_enabled = bool(data["contactless_payments"])
            if old_value != card.is_contactless_enabled:
                changes["contactless_payments"] = {
                    "old": old_value,
                    "new": card.is_contactless_enabled,
                }
        if "international_transactions" in data:
            old_value = card.is_international_enabled
            card.is_international_enabled = bool(data["international_transactions"])
            if old_value != card.is_international_enabled:
                changes["international_transactions"] = {
                    "old": old_value,
                    "new": card.is_international_enabled,
                }
        if "blocked_merchant_categories" in data:
            valid_categories = [
                "gas_stations",
                "grocery_stores",
                "entertainment",
                "travel",
                "online_retail",
                "atm_withdrawals",
                "gambling",
                "adult_entertainment",
                "cryptocurrency",
                "money_transfer",
            ]
            blocked_categories = data["blocked_merchant_categories"]
            if not isinstance(blocked_categories, list):
                raise CardServiceError(
                    "Blocked merchant categories must be a list",
                    "INVALID_CATEGORIES_FORMAT",
                )
            for category in blocked_categories:
                if category not in valid_categories:
                    raise CardServiceError(
                        f"Invalid merchant category: {category}",
                        "INVALID_MERCHANT_CATEGORY",
                    )
            old_categories = json.loads(card.blocked_merchant_categories)
            card.blocked_merchant_categories = json.dumps(blocked_categories)
            if old_categories != blocked_categories:
                changes["blocked_merchant_categories"] = {
                    "old": old_categories,
                    "new": blocked_categories,
                }
        card.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return (card, changes)

    def get_cards_for_account(self, user: User, account_id: str) -> List[Card]:
        """Retrieves all cards linked to a specific account, performing access control."""
        account = Account.query.get(account_id)
        if not account:
            raise CardServiceError("Account not found", "ACCOUNT_NOT_FOUND")
        if account.user_id != user.id and (not user.is_admin):
            raise CardServiceError("Access denied", "ACCESS_DENIED")
        return Card.query.filter_by(account_id=account_id).all()


card_service = CardService()
