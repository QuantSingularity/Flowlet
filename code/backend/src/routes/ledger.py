import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import flask
from flask import Blueprint, g, jsonify, request
from sqlalchemy import func, select

from ..models.audit_log import AuditEventType, AuditSeverity
from ..models.database import db
from ..models.ledger import LedgerAccountType, LedgerEntry
from ..security.audit_logger import audit_logger
from ..utils.auth import admin_required

ledger_bp = Blueprint("ledger", __name__, url_prefix="/ledger")
logger = logging.getLogger(__name__)
CHART_OF_ACCOUNTS = {
    "cash_and_equivalents": {
        "type": LedgerAccountType.ASSET,
        "name": "Cash and Cash Equivalents",
    },
    "customer_deposits": {
        "type": LedgerAccountType.LIABILITY,
        "name": "Customer Deposits",
    },
    "transaction_fees": {
        "type": LedgerAccountType.REVENUE,
        "name": "Transaction Fee Revenue",
    },
    "processing_costs": {
        "type": LedgerAccountType.EXPENSE,
        "name": "Payment Processing Costs",
    },
}


@ledger_bp.route("/entry", methods=["POST"])
@admin_required
def create_journal_entry() -> "flask.Response":
    """Create a journal entry with multiple ledger entries (double-entry bookkeeping)"""
    try:
        data = request.get_json()
        if not data or "entries" not in data:
            return (
                jsonify({"error": "Missing entries data", "code": "MISSING_DATA"}),
                400,
            )
        entries_data = data["entries"]
        total_debits = Decimal("0.00")
        total_credits = Decimal("0.00")
        for entry_data in entries_data:
            debit = Decimal(str(entry_data.get("debit_amount", "0.00")))
            credit = Decimal(str(entry_data.get("credit_amount", "0.00")))
            total_debits += debit
            total_credits += credit
            account_name = entry_data.get("account_name")
            if account_name not in CHART_OF_ACCOUNTS:
                return (
                    jsonify(
                        {
                            "error": f"Invalid account name: {account_name}",
                            "code": "INVALID_ACCOUNT",
                        }
                    ),
                    400,
                )
            if not entry_data.get("currency"):
                return (
                    jsonify(
                        {
                            "error": "Missing currency for entry",
                            "code": "MISSING_CURRENCY",
                        }
                    ),
                    400,
                )
        if total_debits != total_credits:
            return (
                jsonify(
                    {
                        "error": f"Unbalanced entry: Debits ({total_debits}) != Credits ({total_credits})",
                        "code": "UNBALANCED_ENTRY",
                    }
                ),
                400,
            )
        if len(entries_data) < 2:
            return (
                jsonify(
                    {
                        "error": "Journal entry must have at least two entries",
                        "code": "INSUFFICIENT_ENTRIES",
                    }
                ),
                400,
            )
        journal_entry_id = str(uuid.uuid4())
        ledger_entries = []
        for entry_data in entries_data:
            account_name = entry_data["account_name"]
            account_info = CHART_OF_ACCOUNTS[account_name]
            ledger_entry = LedgerEntry(
                transaction_id=data.get("transaction_id"),
                journal_entry_id=journal_entry_id,
                account_type=account_info["type"],
                account_name=account_name,
                debit_amount=Decimal(str(entry_data.get("debit_amount", "0.00"))),
                credit_amount=Decimal(str(entry_data.get("credit_amount", "0.00"))),
                currency=entry_data["currency"],
                description=entry_data.get(
                    "description", data.get("description", "Manual Journal Entry")
                ),
                created_at=datetime.now(timezone.utc),
            )
            ledger_entries.append(ledger_entry)
        db.session.add_all(ledger_entries)
        db.session.commit()
        audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_EVENT,
            description=f"Journal entry created: {journal_entry_id}",
            user_id=g.current_user.id,
            severity=AuditSeverity.MEDIUM,
            resource_type="journal_entry",
            resource_id=journal_entry_id,
        )
        return (
            jsonify(
                {
                    "success": True,
                    "journal_entry_id": journal_entry_id,
                    "total_debits": float(total_debits),
                    "total_credits": float(total_credits),
                    "message": "Journal entry created successfully",
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating journal entry: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )


@ledger_bp.route("/balance/<account_name>", methods=["GET"])
@admin_required
def get_account_balance(account_name: Any) -> "flask.Response":
    """Get the current balance for a specific ledger account"""
    try:
        if account_name not in CHART_OF_ACCOUNTS:
            return (
                jsonify(
                    {
                        "error": f"Account {account_name} not found",
                        "code": "INVALID_ACCOUNT",
                    }
                ),
                404,
            )
        account_info = CHART_OF_ACCOUNTS[account_name]
        is_debit_normal = account_info["type"] in [
            LedgerAccountType.ASSET,
            LedgerAccountType.EXPENSE,
        ]
        balance_query = select(
            func.sum(LedgerEntry.debit_amount).label("total_debit"),
            func.sum(LedgerEntry.credit_amount).label("total_credit"),
        ).filter(LedgerEntry.account_name == account_name)
        result = db.session.execute(balance_query).one_or_none()
        total_debit = (
            result.total_debit if result and result.total_debit else Decimal("0.00")
        )
        total_credit = (
            result.total_credit if result and result.total_credit else Decimal("0.00")
        )
        if is_debit_normal:
            balance = total_debit - total_credit
        else:
            balance = total_credit - total_debit
        return (
            jsonify(
                {
                    "account_name": account_name,
                    "account_type": account_info["type"].value,
                    "balance": float(balance),
                    "total_debit": float(total_debit),
                    "total_credit": float(total_credit),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error getting account balance: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )


@ledger_bp.route("/entries", methods=["GET"])
@admin_required
def get_ledger_entries() -> "flask.Response":
    """Get all ledger entries (Admin only)"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        stmt = select(LedgerEntry).order_by(LedgerEntry.created_at.desc())
        offset = (page - 1) * per_page
        paginated_stmt = stmt.limit(per_page).offset(offset)
        entries = db.session.execute(paginated_stmt).scalars().all()
        count_stmt = select(func.count()).select_from(LedgerEntry)
        total_entries = db.session.execute(count_stmt).scalar_one()
        total_pages = (total_entries + per_page - 1) // per_page
        entry_list = [entry.to_dict() for entry in entries]
        return (
            jsonify(
                {
                    "entries": entry_list,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total_entries,
                        "pages": total_pages,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error getting ledger entries: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )
