import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func, select

from ..models.audit_log import AuditEventType, AuditSeverity
from ..models.database import db
from ..models.fraud_alert import FraudAlert, FraudAlertStatus
from ..models.transaction import Transaction
from ..security.audit_logger import audit_logger
from ..services import ml_gateway
from ..utils.auth import admin_required, token_required
from .ml_common import error_response, int_arg, is_admin, json_body, resolve_target_user

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

try:
    from ml_services.core.exceptions import InvalidTransactionError
except Exception:

    class InvalidTransactionError(Exception):
        pass


try:
    from ml_services.support_chatbot.privacy import redact_pii
except Exception:

    def redact_pii(text: str) -> Any:
        return text, 0


ai_service_bp = Blueprint("ai_service", __name__, url_prefix="/ai")
logger = logging.getLogger(__name__)

MAX_CATEGORIZE = 500
MAX_QUERY_LENGTH = 2000
LLM_CONFIDENCE_FLOOR = 0.4
RESOLUTION_STATUSES = {
    "resolved": FraudAlertStatus.RESOLVED,
    "confirmed": FraudAlertStatus.CONFIRMED,
    "false_positive": FraudAlertStatus.FALSE_POSITIVE,
    "dismissed": FraudAlertStatus.DISMISSED,
    "reviewed": FraudAlertStatus.REVIEWED,
    "investigating": FraudAlertStatus.INVESTIGATING,
}
FEEDBACK_LABELS = {
    FraudAlertStatus.CONFIRMED: True,
    FraudAlertStatus.FALSE_POSITIVE: False,
    FraudAlertStatus.DISMISSED: False,
}


def _llm_client() -> Any:
    if not (OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY")):
        return None
    try:
        return OpenAI()
    except Exception as exc:
        logger.error("Failed to initialize LLM client: %s", exc)
        return None


def _ml() -> Any:
    if not ml_gateway.ml_enabled():
        return None
    return ml_gateway.get_ml()


def _unavailable() -> Any:
    return error_response("AI service is unavailable", "AI_SERVICE_UNAVAILABLE", 503)


@ai_service_bp.route("/health", methods=["GET"])
@token_required
def ai_health() -> object:
    container = _ml()
    if container is None:
        return jsonify({"status": "disabled"}), 200
    return jsonify(container.health()), 200


@ai_service_bp.route("/fraud-detection/analyze", methods=["POST"])
@token_required
def analyze_transaction_fraud() -> object:
    container = _ml()
    if container is None:
        return _unavailable()
    data, failure = json_body(("amount",))
    if failure:
        return failure
    target, denied = resolve_target_user(data.get("user_id"))
    if denied:
        return denied
    merchant = data.get("merchant_info") or {}
    if not isinstance(merchant, dict):
        return error_response(
            "merchant_info must be an object", "INVALID_MERCHANT", 400
        )
    transaction_id = data.get("transaction_id")
    try:
        alert = ml_gateway.score_transaction(
            db.session,
            str(target.id),
            data["amount"],
            str(data.get("currency", "USD")),
            transaction_id=str(transaction_id) if transaction_id else None,
            channel=data.get("channel", "api"),
            merchant_category=merchant.get("category"),
            location_country=(
                merchant.get("location") or data.get("user_location") or None
            ),
            device_fingerprint=data.get("device_fingerprint"),
            ip_address=data.get("ip_address") or request.remote_addr,
            description=merchant.get("name"),
        )
    except InvalidTransactionError as exc:
        return error_response(str(exc), "INVALID_TRANSACTION", 400)
    if alert is None:
        return _unavailable()
    alert_id = None
    if alert.is_flagged:
        record = ml_gateway.persist_alert(db.session, alert, commit=True)
        if record is not None:
            alert_id = record.id
            audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                description=f"Fraud alert created for transaction {alert.transaction_id}",
                user_id=str(target.id),
                severity=AuditSeverity.HIGH,
                resource_type="fraud_alert",
                resource_id=alert_id,
            )
    rule_names = [hit["name"] for hit in alert.explanation.get("rule_hits", [])]
    primary = [
        item["feature"] for item in alert.explanation.get("primary_risk_factors", [])
    ]
    action = {
        "allow": "approve",
        "monitor": "monitor",
        "challenge": "require_additional_verification",
        "review": "require_additional_verification",
        "block": "block_transaction",
    }[alert.action.value]
    return (
        jsonify(
            {
                "transaction_id": alert.transaction_id,
                "fraud_analysis": {
                    "risk_score": round(alert.risk_score * 100.0, 2),
                    "risk_level": alert.risk_level.value,
                    "risk_factors": list(dict.fromkeys(rule_names + primary)),
                    "fraud_types": [t.value for t in alert.fraud_types],
                    "recommended_action": action,
                    "confidence": round(alert.confidence * 100.0, 2),
                    "explanation": alert.explanation,
                },
                "alert_created": alert_id is not None,
                "alert_id": alert_id,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "model_version": alert.model_version,
                "mode": (alert.metadata or {}).get("mode"),
            }
        ),
        200,
    )


@ai_service_bp.route("/fraud-detection/alerts", methods=["GET"])
@token_required
def get_fraud_alerts() -> object:
    page = int_arg("page", 1, 1, 100000)
    per_page = int_arg("per_page", 20, 1, 100)
    conditions = []
    if not is_admin():
        conditions.append(FraudAlert.user_id == str(g.current_user.id))
    elif request.args.get("user_id"):
        conditions.append(FraudAlert.user_id == request.args["user_id"])
    status_arg = request.args.get("status")
    if status_arg:
        status = RESOLUTION_STATUSES.get(status_arg.lower()) or (
            FraudAlertStatus.PENDING if status_arg.lower() == "pending" else None
        )
        if status is None:
            return error_response("Invalid status", "INVALID_STATUS", 400)
        conditions.append(FraudAlert.status == status)
    level = request.args.get("risk_level")
    if level:
        conditions.append(FraudAlert.risk_level == level.lower())
    total = db.session.execute(
        select(func.count()).select_from(FraudAlert).where(*conditions)
    ).scalar_one()
    rows = (
        db.session.execute(
            select(FraudAlert)
            .where(*conditions)
            .order_by(FraudAlert.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        .scalars()
        .all()
    )
    return (
        jsonify(
            {
                "alerts": [row.to_dict(include_details=True) for row in rows],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page,
                },
            }
        ),
        200,
    )


@ai_service_bp.route("/fraud-detection/alerts/<alert_id>/resolve", methods=["POST"])
@admin_required
def resolve_fraud_alert(alert_id: str) -> object:
    data = request.get_json(silent=True) or {}
    resolution = str(data.get("resolution", "resolved")).lower()
    status = RESOLUTION_STATUSES.get(resolution)
    if status is None:
        return error_response("Invalid resolution", "INVALID_RESOLUTION", 400)
    alert = db.session.get(FraudAlert, alert_id)
    if alert is None:
        return error_response("Alert not found", "ALERT_NOT_FOUND", 404)
    alert.status = status
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolved_by = str(g.current_user.id)
    alert.resolution_notes = str(data.get("notes", ""))[:2000]
    db.session.commit()
    feedback_applied = False
    container = _ml()
    if container is not None and status in FEEDBACK_LABELS and alert.transaction_id:
        try:
            feedback_applied = container.fraud.record_feedback(
                alert.transaction_id, FEEDBACK_LABELS[status], "analyst_resolution"
            )
        except Exception as exc:
            logger.warning("Feedback not applied: %s", exc)
    audit_logger.log_event(
        event_type=AuditEventType.SECURITY_ALERT,
        description=f"Fraud alert {alert_id} marked {status.value}",
        user_id=str(g.current_user.id),
        severity=AuditSeverity.MEDIUM,
        resource_type="fraud_alert",
        resource_id=alert_id,
    )
    return (
        jsonify({"alert": alert.to_dict(), "model_feedback_applied": feedback_applied}),
        200,
    )


@ai_service_bp.route("/fraud-detection/alerts/<alert_id>/respond", methods=["POST"])
@token_required
def respond_to_fraud_alert(alert_id: str) -> object:
    data, failure = json_body(("response",))
    if failure:
        return failure
    answer = str(data["response"]).lower()
    outcomes = {
        "recognized": (
            FraudAlertStatus.REVIEWED,
            "Customer recognized the transaction",
        ),
        "not_me": (
            FraudAlertStatus.INVESTIGATING,
            "Customer reported the transaction as unauthorized",
        ),
    }
    if answer not in outcomes:
        return error_response(
            "response must be recognized or not_me", "INVALID_RESPONSE", 400
        )
    alert = db.session.get(FraudAlert, alert_id)
    if alert is None or (alert.user_id != str(g.current_user.id) and not is_admin()):
        return error_response("Alert not found", "ALERT_NOT_FOUND", 404)
    if alert.status not in (
        FraudAlertStatus.PENDING,
        FraudAlertStatus.INVESTIGATING,
        FraudAlertStatus.REVIEWED,
    ):
        return error_response("Alert is already closed", "ALERT_CLOSED", 409)
    status, note = outcomes[answer]
    alert.status = status
    alert.resolution_notes = note
    db.session.commit()
    audit_logger.log_event(
        event_type=AuditEventType.SECURITY_ALERT,
        description=f"Customer responded {answer} to fraud alert {alert_id}",
        user_id=str(g.current_user.id),
        severity=AuditSeverity.MEDIUM if answer == "recognized" else AuditSeverity.HIGH,
        resource_type="fraud_alert",
        resource_id=alert_id,
    )
    return jsonify({"alert": alert.to_dict()}), 200


@ai_service_bp.route("/risk/assess", methods=["POST"])
@token_required
def assess_risk() -> object:
    container = _ml()
    if container is None:
        return _unavailable()
    data = request.get_json(silent=True) or {}
    target, denied = resolve_target_user(data.get("user_id"))
    if denied:
        return denied
    user_data = ml_gateway.build_risk_user_data(db.session, target)
    assessment = container.risk.assess_user_risk(str(target.id), user_data=user_data)
    return jsonify({"assessment": assessment.to_dict()}), 200


@ai_service_bp.route("/risk/report", methods=["GET"])
@token_required
def risk_report() -> object:
    container = _ml()
    if container is None:
        return _unavailable()
    target, denied = resolve_target_user(request.args.get("user_id"))
    if denied:
        return denied
    user_data = ml_gateway.build_risk_user_data(db.session, target)
    return jsonify(container.risk.generate_risk_report(str(target.id), user_data)), 200


@ai_service_bp.route("/transactions/categorize", methods=["POST"])
@token_required
def categorize_transactions() -> object:
    container = _ml()
    if container is None:
        return _unavailable()
    data, failure = json_body()
    if failure:
        return failure
    items = data.get("transactions")
    if items is None:
        items = [data]
    if not isinstance(items, list) or not items or len(items) > MAX_CATEGORIZE:
        return error_response(
            f"Provide between 1 and {MAX_CATEGORIZE} transactions",
            "INVALID_TRANSACTIONS",
            400,
        )
    if not all(isinstance(item, dict) for item in items):
        return error_response(
            "Each transaction must be an object", "INVALID_TRANSACTIONS", 400
        )
    insights = container.categorizer.categorize_batch(items, str(g.current_user.id))
    return (
        jsonify({"count": len(insights), "results": [i.to_dict() for i in insights]}),
        200,
    )


@ai_service_bp.route("/transactions/categorize/correction", methods=["POST"])
@token_required
def correct_category() -> object:
    container = _ml()
    if container is None:
        return _unavailable()
    data, failure = json_body(("transaction", "category"))
    if failure:
        return failure
    if not isinstance(data["transaction"], dict):
        return error_response(
            "transaction must be an object", "INVALID_TRANSACTION", 400
        )
    saved = container.categorizer.update_user_profile(
        str(g.current_user.id), data["transaction"], data["category"]
    )
    if not saved:
        return error_response(
            "Unknown category or empty description", "INVALID_CORRECTION", 400
        )
    return jsonify({"success": True}), 200


@ai_service_bp.route("/spending/analysis", methods=["GET"])
@token_required
def spending_analysis() -> object:
    container = _ml()
    if container is None:
        return _unavailable()
    days = int_arg("days", 90, 7, 365)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.session.execute(
            select(Transaction)
            .where(
                Transaction.user_id == str(g.current_user.id),
                Transaction.created_at >= cutoff,
            )
            .order_by(Transaction.created_at.desc())
            .limit(5000)
        )
        .scalars()
        .all()
    )
    records: List[Dict[str, Any]] = [
        {
            "transaction_id": row.transaction_id,
            "description": row.description,
            "merchant_name": row.merchant_name,
            "amount": float(row.amount),
            "type": row.transaction_type.value if row.transaction_type else None,
            "timestamp": row.created_at,
            "merchant_category_code": row.merchant_category_code,
        }
        for row in rows
    ]
    analysis = container.spending.analyze_spending_patterns(
        str(g.current_user.id), records, days
    )
    return jsonify({"analysis": analysis.to_dict()}), 200


def _llm_answer(client: Any, query: str, context: Dict[str, Any]) -> Any:
    system_prompt = (
        "You are Flowlet, an assistant for a financial technology platform. Answer questions about "
        "accounts, transactions, and general financial topics. Be concise, professional, and "
        "security conscious. Never request passwords or one time codes. You cannot perform actions "
        "directly; direct the user to the relevant app feature."
    )
    facts = f"Balances: {context.get('balances', {})}"
    response = client.chat.completions.create(
        model=os.environ.get("AI_CHAT_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Account facts: {facts}\nQuestion: {query}"},
        ],
        temperature=0.3,
        max_tokens=400,
    )
    return response.choices[0].message.content, getattr(response, "model", None)


@ai_service_bp.route("/chatbot/query", methods=["POST"])
@token_required
def chatbot_query() -> object:
    container = _ml()
    if container is None:
        return _unavailable()
    data, failure = json_body(("query",))
    if failure:
        return failure
    query = str(data["query"])
    if len(query) > MAX_QUERY_LENGTH:
        return error_response("Query is too long", "QUERY_TOO_LONG", 400)
    session_id = data.get("session_id")
    try:
        context = ml_gateway.build_chat_context(db.session, g.current_user)
    except Exception as exc:
        logger.warning("Chat context unavailable: %s", exc)
        context = {}
    reply = container.chatbot.respond(
        str(g.current_user.id), query, session_id, context
    )
    payload = reply.to_dict()
    payload["source"] = "local"
    client = _llm_client()
    if (
        client is not None
        and reply.confidence < LLM_CONFIDENCE_FLOOR
        and not reply.escalate_to_human
    ):
        try:
            safe_query, _ = redact_pii(query)
            text, model = _llm_answer(client, safe_query, context)
            if text:
                payload.update({"response": text, "source": "llm", "model": model})
        except Exception as exc:
            logger.warning("LLM fallback failed, using local answer: %s", exc)
    audit_logger.log_event(
        event_type=AuditEventType.DATA_ACCESS,
        description="Chatbot query processed",
        user_id=str(g.current_user.id),
        severity=AuditSeverity.LOW,
        details={
            "query_length": len(query),
            "query_type": payload["query_type"],
            "source": payload["source"],
        },
    )
    return jsonify(payload), 200
