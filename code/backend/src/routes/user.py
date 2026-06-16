import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import flask
from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError

from ..models.account import Account
from ..models.audit_log import AuditEventType, AuditSeverity
from ..models.database import db
from ..models.transaction import Transaction, TransactionStatus
from ..models.user import User
from ..security.audit_logger import audit_logger
from ..utils.auth import admin_required, token_required
from ..utils.validators import InputValidator

user_bp = Blueprint("user", __name__, url_prefix="/users")
logger = logging.getLogger(__name__)


@user_bp.route("/", methods=["GET"])
@admin_required
def get_users() -> "flask.Response":
    """
    Get all users with pagination and filtering (Admin only)
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        search = request.args.get("search", "").strip()
        kyc_status = request.args.get("kyc_status")
        status = request.args.get("status")
        sort_by = request.args.get("sort_by", "created_at")
        sort_order = request.args.get("sort_order", "desc")
        stmt = select(User)
        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
            stmt = stmt.where(search_filter)
        if kyc_status:
            stmt = stmt.where(User.kyc_status == kyc_status)
        if status:
            is_active = status.lower() == "active"
            stmt = stmt.where(User.is_active == is_active)
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order.lower() == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        offset = (page - 1) * per_page
        paginated_stmt = stmt.limit(per_page).offset(offset)
        users = db.session.execute(paginated_stmt).scalars().all()
        count_stmt = select(func.count()).select_from(User)
        if search or kyc_status or status:
            count_stmt = select(func.count()).select_from(stmt.subquery())
        total_users = db.session.execute(count_stmt).scalar_one()
        total_pages = (total_users + per_page - 1) // per_page
        user_list = []
        for user in users:
            accounts = (
                db.session.execute(select(Account).filter_by(user_id=user.id))
                .scalars()
                .all()
            )
            total_balance = sum((account.balance for account in accounts))
            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "kyc_status": user.kyc_status,
                "is_active": user.is_active,
                "email_verified": user.email_verified,
                "two_factor_enabled": user.two_factor_enabled,
                "last_login_at": (
                    user.last_login_at.isoformat() if user.last_login_at else None
                ),
                "created_at": user.created_at.isoformat(),
                "account_summary": {
                    "total_accounts": len(accounts),
                    "total_balance": float(total_balance),
                    "primary_currency": accounts[0].currency if accounts else None,
                },
            }
            user_list.append(user_data)
        return (
            jsonify(
                {
                    "success": True,
                    "users": user_list,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total_users,
                        "pages": total_pages,
                        "has_next": page < total_pages,
                        "has_prev": page > 1,
                    },
                    "filters": {
                        "search": search,
                        "kyc_status": kyc_status,
                        "status": status,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Get users error: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Failed to retrieve users", "code": "GET_USERS_ERROR"}),
            500,
        )


@user_bp.route("/<user_id>", methods=["GET"])
@token_required
def get_user(user_id: Any) -> "flask.Response":
    """Get user details by ID (Admin or own profile)"""
    try:
        current_user = g.current_user
        if current_user.id != user_id and (not current_user.is_admin):
            return (jsonify({"error": "Access denied", "code": "ACCESS_DENIED"}), 403)
        user = db.session.get(User, user_id)
        if not user:
            return (jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}), 404)
        accounts = (
            db.session.execute(select(Account).filter_by(user_id=user.id))
            .scalars()
            .all()
        )
        account_data = []
        for account in accounts:
            account_data.append(
                {
                    "id": account.id,
                    "account_name": account.account_name,
                    "account_type": account.account_type.value,
                    "currency": account.currency,
                    "available_balance": float(account.balance),
                    "current_balance": float(account.balance),
                    "status": account.status.value,
                    "created_at": account.created_at.isoformat(),
                }
            )
        recent_transactions_stmt = (
            select(Transaction)
            .filter_by(user_id=user.id)
            .order_by(Transaction.created_at.desc())
            .limit(10)
        )
        recent_transactions = (
            db.session.execute(recent_transactions_stmt).scalars().all()
        )
        transaction_data = []
        for transaction in recent_transactions:
            transaction_data.append(
                {
                    "id": transaction.id,
                    "type": transaction.transaction_type.value,
                    "category": transaction.transaction_category.value,
                    "amount": float(transaction.amount),
                    "currency": transaction.currency,
                    "description": transaction.description,
                    "status": transaction.status.value,
                    "created_at": transaction.created_at.isoformat(),
                }
            )
        total_balance = sum((account.balance for account in accounts))
        total_transactions_stmt = (
            select(func.count()).select_from(Transaction).filter_by(user_id=user.id)
        )
        total_transactions = db.session.execute(total_transactions_stmt).scalar_one()
        current_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        monthly_volume_stmt = select(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.user_id == user.id,
                Transaction.created_at >= current_month,
                Transaction.status == TransactionStatus.COMPLETED,
            )
        )
        monthly_volume = db.session.execute(
            monthly_volume_stmt
        ).scalar_one_or_none() or Decimal("0.00")
        user_data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "date_of_birth": (
                user.date_of_birth.isoformat() if user.date_of_birth else None
            ),
            "address": (
                {
                    "street": user.address_street,
                    "city": user.address_city,
                    "state": user.address_state,
                    "postal_code": user.address_postal_code,
                    "country": user.address_country,
                }
                if user.address_street
                else None
            ),
            "kyc_status": user.kyc_status,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "two_factor_enabled": user.two_factor_enabled,
            "last_login_at": (
                user.last_login_at.isoformat() if user.last_login_at else None
            ),
            "last_login_ip": user.last_login_ip,
            "failed_login_attempts": user.failed_login_attempts,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }
        return (
            jsonify(
                {
                    "success": True,
                    "user": user_data,
                    "accounts": account_data,
                    "recent_transactions": transaction_data,
                    "statistics": {
                        "total_accounts": len(accounts),
                        "total_balance": float(total_balance),
                        "total_transactions": total_transactions,
                        "monthly_volume": float(monthly_volume),
                        "account_age_days": (
                            datetime.now(timezone.utc) - user.created_at
                        ).days,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Get user error: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Failed to retrieve user", "code": "GET_USER_ERROR"}),
            500,
        )


@user_bp.route("/<user_id>", methods=["PUT"])
@token_required
def update_user(user_id: Any) -> None:
    """Update user details (Admin or own profile)"""
    try:
        current_user = g.current_user
        if current_user.id != user_id and (not current_user.is_admin):
            return (jsonify({"error": "Access denied", "code": "ACCESS_DENIED"}), 403)
        user = db.session.get(User, user_id)
        if not user:
            return (jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}), 404)
        data = request.get_json()
        if not data:
            return (
                jsonify(
                    {
                        "error": "Request body must contain valid JSON",
                        "code": "INVALID_JSON",
                    }
                ),
                400,
            )
        updatable_fields = ["first_name", "last_name", "phone", "date_of_birth"]
        admin_fields = ["is_active", "is_admin", "kyc_status"]
        for field in updatable_fields:
            if field in data:
                if field == "date_of_birth":
                    is_valid, message, dob = InputValidator.validate_date(
                        data[field], "%Y-%m-%d"
                    )
                    if not is_valid:
                        return (
                            jsonify({"error": message, "code": "INVALID_DATE_FORMAT"}),
                            400,
                        )
                    setattr(user, field, dob)
                else:
                    setattr(user, field, data[field])
        if current_user.is_admin:
            for field in admin_fields:
                if field in data:
                    setattr(user, field, data[field])
        if "address" in data and isinstance(data["address"], dict):
            address_data = data["address"]
            user.address_street = address_data.get("street", user.address_street)
            user.address_city = address_data.get("city", user.address_city)
            user.address_state = address_data.get("state", user.address_state)
            user.address_postal_code = address_data.get(
                "postal_code", user.address_postal_code
            )
            user.address_country = address_data.get("country", user.address_country)
        db.session.commit()
        audit_logger.log_event(
            event_type=AuditEventType.ACCOUNT_MODIFICATION,
            description=f"User details updated for user: {user_id}",
            user_id=current_user.id,
            severity=(
                AuditSeverity.MEDIUM if current_user.is_admin else AuditSeverity.LOW
            ),
            details={"updated_fields": list(data.keys())},
        )
        return (
            jsonify(
                {"message": "User details updated successfully", "user_id": user.id}
            ),
            200,
        )
    except IntegrityError:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "A user with this email or phone already exists",
                    "code": "INTEGRITY_ERROR",
                }
            ),
            409,
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update user error: {str(e)}", exc_info=True)
        return (
            jsonify(
                {"error": "Failed to update user details", "code": "UPDATE_USER_ERROR"}
            ),
            500,
        )


@user_bp.route("/<user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id: Any) -> "flask.Response":
    """Delete a user (Admin only)"""
    try:
        user = db.session.get(User, user_id)
        if not user:
            return (jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}), 404)
        if g.current_user.id == user_id:
            return (
                jsonify(
                    {
                        "error": "Cannot delete your own admin account",
                        "code": "SELF_DELETE_FORBIDDEN",
                    }
                ),
                403,
            )
        user.is_active = False
        user.email = f"deleted_{user.id}@deleted.com"
        user.phone = None
        user.first_name = "Deleted"
        user.last_name = "User"
        user.password_hash = "DELETED"
        user.two_factor_secret = None
        user.two_factor_enabled = False
        user.kyc_status = "revoked"
        db.session.commit()
        audit_logger.log_event(
            event_type=AuditEventType.ACCOUNT_MODIFICATION,
            description=f"User account soft-deleted: {user_id}",
            user_id=g.current_user.id,
            severity=AuditSeverity.CRITICAL,
            resource_type="user",
            resource_id=user_id,
        )
        return (
            jsonify(
                {
                    "message": "User account soft-deleted successfully",
                    "user_id": user_id,
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete user error: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Failed to delete user", "code": "DELETE_USER_ERROR"}),
            500,
        )
