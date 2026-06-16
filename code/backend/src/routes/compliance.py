import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import flask
from flask import Blueprint, g, jsonify, request
from sqlalchemy import select

from ..models.account import Account
from ..models.audit_log import AuditEventType, AuditSeverity
from ..models.database import db
from ..models.transaction import Transaction, TransactionType
from ..models.user import User
from ..security.audit_logger import audit_logger
from ..utils.auth import admin_required

compliance_bp = Blueprint("compliance", __name__, url_prefix="/compliance")
logger = logging.getLogger(__name__)


@compliance_bp.route("/sar-report", methods=["POST"])
@admin_required
def generate_sar_report() -> str:
    """Generate a Suspicious Activity Report (SAR) for a user."""
    try:
        data = request.get_json()
        required_fields = [
            "user_id",
            "suspicious_activity_description",
            "activity_type",
        ]
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
        user_id = data["user_id"]
        user = db.session.get(User, user_id)
        if not user:
            return (jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}), 404)
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
        accounts_stmt = select(Account.id).filter_by(user_id=user_id)
        account_ids = db.session.execute(accounts_stmt).scalars().all()
        transactions_stmt = (
            select(Transaction)
            .filter(
                Transaction.account_id.in_(account_ids),
                Transaction.created_at >= ninety_days_ago,
            )
            .order_by(Transaction.created_at.desc())
        )
        transactions = db.session.execute(transactions_stmt).scalars().all()
        total_amount = sum((t.amount for t in transactions))
        sar_data = {
            "report_id": f"SAR_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "report_date": datetime.now(timezone.utc).isoformat(),
            "subject_information": {
                "user_id": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email,
                "kyc_status": user.kyc_status,
                "risk_score": user.risk_score,
            },
            "suspicious_activity": {
                "description": data["suspicious_activity_description"],
                "activity_type": data["activity_type"],
                "date_range": {
                    "start": ninety_days_ago.isoformat(),
                    "end": datetime.now(timezone.utc).isoformat(),
                },
                "total_amount_in_period": float(total_amount),
                "transaction_count": len(transactions),
            },
            "transactions_summary": [t.to_dict() for t in transactions],
            "filing_institution": {
                "name": "Flowlet Financial Services",
                "contact_user_id": g.current_user.id,
            },
        }
        audit_logger.log_event(
            event_type=AuditEventType.COMPLIANCE_REPORT,
            description=f"SAR report generated for user {user_id}",
            user_id=g.current_user.id,
            severity=AuditSeverity.HIGH,
            resource_type="sar_report",
            resource_id=sar_data["report_id"],
        )
        return (jsonify(sar_data), 200)
    except Exception as e:
        logger.error(f"SAR report generation error: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )


@compliance_bp.route("/ctr-report", methods=["GET"])
@admin_required
def get_ctr_report() -> "flask.Response":
    """Generate a Currency Transaction Report (CTR) for transactions over $10,000 in a day."""
    try:
        ctr_threshold = Decimal("10000.00")
        transactions_stmt = (
            select(Transaction)
            .filter(
                Transaction.amount >= ctr_threshold,
                Transaction.transaction_type.in_(
                    [TransactionType.CREDIT, TransactionType.DEBIT]
                ),
            )
            .order_by(Transaction.created_at.desc())
            .limit(100)
        )
        transactions = db.session.execute(transactions_stmt).scalars().all()
        ctr_reports = []
        for t in transactions:
            user = db.session.get(User, t.user_id)
            if user:
                ctr_reports.append(
                    {
                        "report_id": f"CTR_{t.id}",
                        "report_date": datetime.now(timezone.utc).isoformat(),
                        "customer_information": {
                            "user_id": user.id,
                            "name": f"{user.first_name} {user.last_name}",
                            "email": user.email,
                        },
                        "transaction_details": t.to_dict(),
                        "reason": f"Single transaction amount {float(t.amount)} exceeds ${float(ctr_threshold)} threshold.",
                    }
                )
        audit_logger.log_event(
            event_type=AuditEventType.COMPLIANCE_REPORT,
            description=f"CTR report generated with {len(ctr_reports)} potential reports",
            user_id=g.current_user.id,
            severity=AuditSeverity.LOW,
            resource_type="ctr_report",
        )
        return (
            jsonify(
                {
                    "total_reports": len(ctr_reports),
                    "ctr_reports": ctr_reports,
                    "note": "This is a simplified CTR report based on single transactions over $10,000. A full CTR requires daily aggregation.",
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"CTR report generation error: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )


@compliance_bp.route("/watchlist-screening", methods=["POST"])
@admin_required
def watchlist_screening() -> object:
    """Simulate screening a user against watchlists."""
    try:
        data = request.get_json()
        required_fields = ["user_id"]
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
        user_id = data["user_id"]
        user = db.session.get(User, user_id)
        if not user:
            return (jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}), 404)
        name = f"{user.first_name} {user.last_name}".strip().lower()
        high_risk_names = ["john doe", "jane smith", "terrorist"]
        screening_results = {
            "user_id": user_id,
            "screening_date": datetime.now(timezone.utc).isoformat(),
            "sources_checked": ["OFAC_SDN", "UN_SANCTIONS", "PEP_LIST"],
            "matches": [],
            "overall_status": "clear",
        }
        if any((hr_name in name for hr_name in high_risk_names)):
            screening_results["matches"].append(
                {
                    "source": "OFAC_SDN",
                    "matched_name": name,
                    "confidence": 95,
                    "match_type": "name_match",
                    "list_entry": {"reason": "Simulated match for high-risk name"},
                }
            )
            screening_results["overall_status"] = "blocked"
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            description=f"Watchlist screening performed for user {user_id}. Status: {screening_results['overall_status']}",
            user_id=g.current_user.id,
            severity=(
                AuditSeverity.MEDIUM
                if screening_results["overall_status"] != "clear"
                else AuditSeverity.LOW
            ),
            resource_type="user",
            resource_id=user_id,
        )
        return (jsonify(screening_results), 200)
    except Exception as e:
        logger.error(f"Watchlist screening error: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )


@compliance_bp.route("/screening/watchlist", methods=["POST"])
def watchlist_screening_compat():
    """Watchlist screening stub."""
    return (
        jsonify({"screening_result": "clear", "matches": [], "risk_level": "low"}),
        200,
    )


@compliance_bp.route("/dashboard", methods=["GET"])
def compliance_dashboard_compat():
    """Compliance dashboard stub."""
    return jsonify({"status": "ok", "alerts": [], "compliance_score": 100}), 200


@compliance_bp.route("/sanctions/screen", methods=["POST"])
def sanctions_screen_compat():
    """Sanctions screening stub."""
    return (
        jsonify({"screening_result": "clear", "matches": [], "risk_level": "low"}),
        200,
    )
