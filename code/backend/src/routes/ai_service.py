import logging
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import flask
from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_, func, select

from ..models.audit_log import AuditEventType, AuditSeverity
from ..models.database import db
from ..models.fraud_alert import FraudAlert, FraudAlertStatus
from ..models.transaction import Transaction
from ..models.user import User
from ..security.audit_logger import audit_logger
from ..utils.auth import admin_required, token_required

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

ai_service_bp = Blueprint("ai_service", __name__, url_prefix="/ai")
logger = logging.getLogger(__name__)
try:
    openai_client = (
        OpenAI() if (OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY")) else None
    )
    logger.info("OpenAI client initialized for AI services.")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    openai_client = None


def _get_risk_level(risk_score: int) -> str:
    """Helper to determine risk level from score."""
    if risk_score >= 70:
        return "high"
    elif risk_score >= 40:
        return "medium"
    elif risk_score >= 20:
        return "low"
    else:
        return "very_low"


@ai_service_bp.route("/fraud-detection/analyze", methods=["POST"])
@token_required
def analyze_transaction_fraud() -> object:
    """Analyze a transaction for potential fraud using AI algorithms (simulated)"""
    try:
        data = request.get_json()
        required_fields = ["transaction_id", "user_id", "amount", "merchant_info"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify(
                        {
                            "error": f"Missing required field: {field}",
                            "code": "MISSING_FIELD",
                        }
                    ),
                    400,
                )
        transaction_id = data["transaction_id"]
        user_id = data["user_id"]
        try:
            amount = Decimal(str(data["amount"]))
        except Exception:
            return (
                jsonify({"error": "Invalid amount format", "code": "INVALID_AMOUNT"}),
                400,
            )
        merchant_info = data["merchant_info"]
        user = db.session.get(User, user_id)
        if not user:
            return (jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}), 404)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_transactions_stmt = (
            select(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= thirty_days_ago,
            )
            .order_by(Transaction.created_at.desc())
            .limit(50)
        )
        recent_transactions = (
            db.session.execute(recent_transactions_stmt).scalars().all()
        )
        risk_factors = []
        risk_score = 0
        if recent_transactions:
            total_amount = sum((t.amount for t in recent_transactions))
            avg_amount = (
                total_amount / len(recent_transactions)
                if len(recent_transactions) > 0
                else Decimal("0.00")
            )
            if amount > avg_amount * 5 and avg_amount > Decimal("10.00"):
                risk_score += 30
                risk_factors.append("unusually_high_amount")
            elif amount > avg_amount * 3 and avg_amount > Decimal("10.00"):
                risk_score += 15
                risk_factors.append("high_amount")
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_count = len(
            [t for t in recent_transactions if t.created_at >= one_hour_ago]
        )
        if recent_count > 10:
            risk_score += 40
            risk_factors.append("high_velocity")
        elif recent_count > 5:
            risk_score += 20
            risk_factors.append("moderate_velocity")
        user_location = data.get("user_location", "US")
        merchant_location = merchant_info.get("location", "US")
        if user_location != merchant_location:
            risk_score += 25
            risk_factors.append("geographic_mismatch")
        current_hour = datetime.now(timezone.utc).hour
        if current_hour < 6 or current_hour > 23:
            risk_score += 15
            risk_factors.append("unusual_time")
        merchant_category = merchant_info.get("category", "unknown")
        high_risk_categories = ["gambling", "adult_entertainment", "cryptocurrency"]
        if merchant_category in high_risk_categories:
            risk_score += 35
            risk_factors.append("high_risk_merchant")
        risk_level = _get_risk_level(risk_score)
        recommended_action = "approve"
        if risk_level == "high":
            recommended_action = "block_transaction"
        elif risk_level == "medium":
            recommended_action = "require_additional_verification"
        elif risk_level == "low":
            recommended_action = "monitor"
        alert_id = None
        if risk_score >= 40:
            alert = FraudAlert(
                transaction_id=transaction_id,
                user_id=user_id,
                alert_type="suspicious_transaction",
                risk_score=risk_score,
                description=f"AI detected suspicious transaction: {', '.join(risk_factors)}",
                status=FraudAlertStatus.OPEN,
            )
            db.session.add(alert)
            db.session.commit()
            alert_id = alert.id
            audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                description=f"Fraud alert created for transaction {transaction_id}",
                user_id=user_id,
                severity=AuditSeverity.HIGH,
                resource_type="fraud_alert",
                resource_id=alert_id,
            )
        return (
            jsonify(
                {
                    "transaction_id": transaction_id,
                    "fraud_analysis": {
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "risk_factors": risk_factors,
                        "recommended_action": recommended_action,
                        "confidence": min(95, 60 + risk_score // 5),
                    },
                    "alert_created": alert_id is not None,
                    "alert_id": alert_id,
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "model_version": "FlowletAI-FraudDetection-v2.1",
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fraud analysis error: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )


@ai_service_bp.route("/fraud-detection/alerts", methods=["GET"])
@admin_required
def get_fraud_alerts() -> "flask.Response":
    """Get fraud alerts with filtering (Admin only)"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")
        risk_level = request.args.get("risk_level")
        user_id = request.args.get("user_id")
        stmt = select(FraudAlert)
        if status:
            try:
                status_enum = FraudAlertStatus(status.lower())
                stmt = stmt.where(FraudAlert.status == status_enum)
            except ValueError:
                return (
                    jsonify(
                        {"error": "Invalid status filter", "code": "INVALID_FILTER"}
                    ),
                    400,
                )
        if user_id:
            stmt = stmt.where(FraudAlert.user_id == user_id)
        if risk_level:
            if risk_level == "high":
                stmt = stmt.where(FraudAlert.risk_score >= 70)
            elif risk_level == "medium":
                stmt = stmt.where(
                    and_(FraudAlert.risk_score >= 40, FraudAlert.risk_score < 70)
                )
            elif risk_level == "low":
                stmt = stmt.where(
                    and_(FraudAlert.risk_score >= 20, FraudAlert.risk_score < 40)
                )
            elif risk_level == "very_low":
                stmt = stmt.where(FraudAlert.risk_score < 20)
        offset = (page - 1) * per_page
        paginated_stmt = (
            stmt.order_by(FraudAlert.created_at.desc()).limit(per_page).offset(offset)
        )
        alerts = db.session.execute(paginated_stmt).scalars().all()
        count_stmt = (
            select(func.count()).select_from(FraudAlert).filter(stmt.whereclause)
        )
        total_alerts = db.session.execute(count_stmt).scalar_one()
        total_pages = (total_alerts + per_page - 1) // per_page
        alert_list = [alert.to_dict() for alert in alerts]
        return (
            jsonify(
                {
                    "alerts": alert_list,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total_alerts,
                        "pages": total_pages,
                        "has_next": page < total_pages,
                        "has_prev": page > 1,
                    },
                    "filters_applied": {
                        "status": status,
                        "risk_level": risk_level,
                        "user_id": user_id,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Get fraud alerts error: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )


@ai_service_bp.route("/fraud-detection/alerts/<alert_id>/resolve", methods=["POST"])
@admin_required
def resolve_fraud_alert(alert_id: Any) -> object:
    """Resolve a fraud alert (Admin only)"""
    try:
        data = request.get_json()
        alert = db.session.get(FraudAlert, alert_id)
        if not alert:
            return (
                jsonify({"error": "Alert not found", "code": "ALERT_NOT_FOUND"}),
                404,
            )
        resolution = data.get("resolution", "resolved").lower()
        notes = data.get("notes", "")
        try:
            resolution_status = FraudAlertStatus(resolution)
        except ValueError:
            return (
                jsonify(
                    {"error": "Invalid resolution status", "code": "INVALID_RESOLUTION"}
                ),
                400,
            )
        alert.status = resolution_status
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolution_notes = notes
        db.session.commit()
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            description=f"Fraud alert {alert_id} resolved as {resolution}",
            user_id=g.current_user.id,
            severity=AuditSeverity.MEDIUM,
            resource_type="fraud_alert",
            resource_id=alert_id,
        )
        return (
            jsonify(
                {
                    "alert_id": alert.id,
                    "status": alert.status.value,
                    "resolved_at": alert.resolved_at.isoformat(),
                    "message": "Alert resolved successfully",
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Resolve fraud alert error: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
            500,
        )


@ai_service_bp.route("/chatbot/query", methods=["POST"])
@token_required
def chatbot_query() -> object:
    """AI Support Chatbot for user assistance"""
    if not openai_client:
        return (
            jsonify(
                {"error": "AI service not available", "code": "AI_SERVICE_UNAVAILABLE"}
            ),
            503,
        )
    try:
        data = request.get_json()
        if "query" not in data:
            return (
                jsonify(
                    {"error": "Missing required field: query", "code": "MISSING_FIELD"}
                ),
                400,
            )
        user_query = data["query"]
        system_prompt = "You are Flowlet, an AI assistant for a modern financial technology platform. Your purpose is to answer user questions about their accounts, transactions, and general financial queries. Be helpful, professional, and security-conscious. Do not disclose any sensitive user information. If a query requires an action like a transfer or a change of settings, instruct the user to use the appropriate API endpoint or application feature, as you cannot perform actions directly."
        user_context = f"User ID: {g.current_user.id}\nUser Email: {g.current_user.email}\nAccount Status: {('Active' if g.current_user.is_active else 'Inactive')}\nKYC Status: {g.current_user.kyc_status}\nTime: {datetime.now(timezone.utc).isoformat()}\n"
        response = openai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"User Context: {user_context}\nQuery: {user_query}",
                },
            ],
            temperature=0.7,
            max_tokens=500,
        )
        ai_response = response.choices[0].message.content
        audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            description="Chatbot query processed",
            user_id=g.current_user.id,
            severity=AuditSeverity.LOW,
            details={"query": user_query},
        )
        return (
            jsonify(
                {
                    "response": ai_response,
                    "model": response.model,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Chatbot query error: {str(e)}", exc_info=True)
        return (
            jsonify(
                {
                    "error": "AI service failed to process request",
                    "code": "AI_PROCESSING_ERROR",
                }
            ),
            500,
        )
