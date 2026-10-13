import logging
from typing import Any

import pandas as pd
from flask import Blueprint, jsonify, request

from ..services.ml_gateway import get_ml, ml_enabled
from ..utils.auth import admin_required, token_required
from .ml_common import error_response, int_arg, is_admin, json_body

try:
    from ml_services.core.enums import RiskLevel
    from ml_services.core.exceptions import FraudDetectionError, MLServiceError
except Exception:

    class MLServiceError(Exception):
        pass

    class FraudDetectionError(MLServiceError):
        pass

    RiskLevel = None

logger = logging.getLogger(__name__)
fraud_detection_bp = Blueprint("fraud", __name__, url_prefix="/fraud")

MAX_BATCH = 500
MAX_TRAINING_ROWS = 200000


def _service() -> Any:
    container = get_ml()
    if container is None or not ml_enabled():
        return None
    return container.fraud


def _unavailable() -> Any:
    return error_response("Fraud detection is unavailable", "ML_UNAVAILABLE", 503)


def _scope_user(payload: dict) -> dict:
    from flask import g

    scoped = dict(payload)
    if not is_admin() or not scoped.get("user_id"):
        scoped["user_id"] = str(g.current_user.id)
    return scoped


@fraud_detection_bp.route("/detect", methods=["POST"])
@token_required
def detect_fraud() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    data, failure = json_body(("amount",))
    if failure:
        return failure
    alert = service.detect(_scope_user(data))
    return jsonify({"success": True, "alert": alert.to_dict()}), 200


@fraud_detection_bp.route("/detect/batch", methods=["POST"])
@admin_required
def detect_fraud_batch() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    data, failure = json_body(("transactions",))
    if failure:
        return failure
    transactions = data["transactions"]
    if not isinstance(transactions, list) or not transactions:
        return error_response(
            "transactions must be a non-empty list", "INVALID_TRANSACTIONS", 400
        )
    if len(transactions) > MAX_BATCH:
        return error_response(
            f"At most {MAX_BATCH} transactions per batch", "BATCH_TOO_LARGE", 413
        )
    alerts = service.batch_detect(transactions)
    return (
        jsonify(
            {
                "success": True,
                "count": len(alerts),
                "alerts": [alert.to_dict(include_details=False) for alert in alerts],
            }
        ),
        200,
    )


@fraud_detection_bp.route("/analyze", methods=["POST"])
@token_required
def analyze_transaction() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    data, failure = json_body(("amount",))
    if failure:
        return failure
    return (
        jsonify(
            {
                "success": True,
                "analysis": service.analyze_transaction(_scope_user(data)),
            }
        ),
        200,
    )


@fraud_detection_bp.route("/anomalies", methods=["POST"])
@token_required
def detect_anomalies() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    data, failure = json_body(("amount",))
    if failure:
        return failure
    return (
        jsonify({"success": True, **service.detect_anomalies(_scope_user(data))}),
        200,
    )


@fraud_detection_bp.route("/velocity", methods=["POST"])
@token_required
def check_velocity() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    data, failure = json_body()
    if failure:
        return failure
    scoped = _scope_user(data)
    result = service.check_velocity(
        scoped["user_id"],
        data.get("transactions") or data.get("amount"),
        data.get("currency", "USD"),
    )
    return jsonify({"success": True, **result}), 200


@fraud_detection_bp.route("/model/train", methods=["POST"])
@admin_required
def train_model() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    data, failure = json_body()
    if failure:
        return failure
    if data.get("synthetic"):
        result = service.bootstrap(data.get("samples"))
    elif data.get("transactions"):
        records = data["transactions"]
        if not isinstance(records, list) or len(records) > MAX_TRAINING_ROWS:
            return error_response(
                "transactions must be a list within the size limit",
                "INVALID_TRAINING_DATA",
                400,
            )
        result = service.train_from_transactions(
            records, data.get("label_key", "is_fraud")
        )
    else:
        rows = data.get("training_data")
        labels = data.get("labels")
        if not isinstance(rows, list) or not rows or labels is None:
            return error_response(
                "training_data and labels are required", "MISSING_TRAINING_DATA", 400
            )
        if len(rows) > MAX_TRAINING_ROWS or len(rows) != len(labels):
            return error_response(
                "training_data and labels must match and stay within limits",
                "INVALID_TRAINING_DATA",
                400,
            )
        validation = None
        if data.get("validation_data") and data.get("validation_labels"):
            validation = (
                pd.DataFrame(data["validation_data"]),
                data["validation_labels"],
            )
        result = service.train_model_sync(
            pd.DataFrame(rows), labels, validation, True, "supplied"
        )
    return jsonify({"success": True, "result": result}), 200


@fraud_detection_bp.route("/model/retrain", methods=["POST"])
@admin_required
def retrain_model() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    data = request.get_json(silent=True) or {}
    result = service.retrain_from_feedback(force=bool(data.get("force", False)))
    return jsonify({"success": True, "result": result}), 200


@fraud_detection_bp.route("/model/status", methods=["GET"])
@admin_required
def get_model_status() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    return jsonify({"success": True, "status": service.get_model_status()}), 200


@fraud_detection_bp.route("/model/drift", methods=["GET"])
@admin_required
def get_drift() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    return jsonify({"success": True, "drift": service.drift_report()}), 200


@fraud_detection_bp.route("/model/retrain/check", methods=["GET"])
@admin_required
def check_retrain_needed() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    reasons = service.retrain_reasons()
    return (
        jsonify(
            {
                "success": True,
                "retrain_needed": bool(reasons),
                "reasons": reasons,
                "auto_retrain": service.auto_retrain,
            }
        ),
        200,
    )


@fraud_detection_bp.route("/alerts", methods=["GET"])
@admin_required
def get_recent_alerts() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    hours = int_arg("hours", 24, 1, 24 * 90)
    limit = int_arg("limit", 100, 1, 1000)
    raw_levels = request.args.get("risk_levels", "")
    levels = []
    for item in [
        part.strip().lower() for part in raw_levels.split(",") if part.strip()
    ]:
        try:
            levels.append(RiskLevel(item))
        except ValueError:
            return error_response(
                f"Invalid risk level: {item}", "INVALID_RISK_LEVEL", 400
            )
    alerts = service.get_recent_alerts(hours, levels or None, limit)
    return (
        jsonify(
            {
                "success": True,
                "count": len(alerts),
                "alerts": [alert.to_dict(include_details=False) for alert in alerts],
            }
        ),
        200,
    )


@fraud_detection_bp.route("/statistics", methods=["GET"])
@admin_required
def get_fraud_statistics() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    hours = int_arg("hours", 24, 1, 24 * 90)
    return (
        jsonify({"success": True, "statistics": service.get_fraud_statistics(hours)}),
        200,
    )


@fraud_detection_bp.route("/feedback", methods=["POST"])
@admin_required
def submit_feedback() -> object:
    service = _service()
    if service is None:
        return _unavailable()
    data, failure = json_body(("transaction_id", "is_fraud"))
    if failure:
        return failure
    if not isinstance(data["is_fraud"], bool):
        return error_response("is_fraud must be a boolean", "INVALID_FEEDBACK", 400)
    recorded = service.record_feedback(
        str(data["transaction_id"]),
        data["is_fraud"],
        str(data.get("feedback_type", "manual_review")),
    )
    if not recorded:
        return error_response(
            "Transaction not found in recent alerts", "TRANSACTION_NOT_FOUND", 404
        )
    return jsonify({"success": True, "message": "Feedback recorded"}), 200


@fraud_detection_bp.route("/health", methods=["GET"])
def health_check() -> object:
    service = _service()
    if service is None:
        return jsonify({"status": "disabled"}), 200
    health = service.health()
    return jsonify({"status": health["status"], "mode": health["mode"]}), 200


@fraud_detection_bp.errorhandler(MLServiceError)
def handle_ml_error(error: Exception) -> object:
    logger.warning("ML service error: %s", error)
    if isinstance(error, FraudDetectionError):
        return error_response(str(error), "FRAUD_DETECTION_ERROR", 400)
    return error_response("ML service error", "ML_ERROR", 500)
