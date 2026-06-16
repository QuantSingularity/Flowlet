import asyncio
import logging
from datetime import datetime
from typing import Any

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False
import flask
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from ml_services.fraud_detection import FraudDetectionError, RiskLevel
from ml_services.fraud_detection.service import get_fraud_service

"\nFlask Routes for Fraud Detection\nProvides REST API endpoints for fraud detection functionality\n"
logger = logging.getLogger(__name__)
fraud_detection_bp = Blueprint("fraud", __name__, url_prefix="/fraud")


@fraud_detection_bp.route("/detect", methods=["POST"])
@cross_origin()
def detect_fraud() -> object:
    """Detect fraud for a single transaction"""
    try:
        data = request.get_json()
        required_fields = [
            "transaction_id",
            "user_id",
            "amount",
            "currency",
            "timestamp",
        ]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify(
                        {"success": False, "error": f"Missing required field: {field}"}
                    ),
                    400,
                )
        fraud_service = get_fraud_service()
        user_history = None
        if "user_history" in data and data["user_history"]:
            user_history = pd.DataFrame(data["user_history"])
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        alert = loop.run_until_complete(fraud_service.detect_fraud(data, user_history))
        loop.close()
        alert_data = {
            "alert_id": alert.alert_id,
            "transaction_id": alert.transaction_id,
            "user_id": alert.user_id,
            "risk_score": alert.risk_score,
            "risk_level": alert.risk_level.value,
            "fraud_types": [ft.value for ft in alert.fraud_types],
            "confidence": alert.confidence,
            "timestamp": alert.timestamp.isoformat(),
            "features_used": alert.features_used,
            "model_version": alert.model_version,
            "explanation": alert.explanation,
            "recommended_actions": alert.recommended_actions,
        }
        return (jsonify({"success": True, "alert": alert_data}), 200)
    except FraudDetectionError as e:
        return (jsonify({"success": False, "error": str(e)}), 400)
    except Exception as e:
        logger.error(f"Fraud detection failed: {str(e)}")
        return (jsonify({"success": False, "error": str(e)}), 500)


@fraud_detection_bp.route("/detect/batch", methods=["POST"])
@cross_origin()
def detect_fraud_batch() -> object:
    """Detect fraud for multiple transactions"""
    try:
        data = request.get_json()
        if "transactions" not in data:
            return (
                jsonify(
                    {"success": False, "error": "Missing required field: transactions"}
                ),
                400,
            )
        transactions = data["transactions"]
        user_histories = data.get("user_histories", {})
        processed_histories = {}
        for user_id, history in user_histories.items():
            if history:
                processed_histories[user_id] = pd.DataFrame(history)
        fraud_service = get_fraud_service()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        alerts = loop.run_until_complete(
            fraud_service.batch_detect_fraud(transactions, processed_histories)
        )
        loop.close()
        alerts_data = []
        for alert in alerts:
            alert_data = {
                "alert_id": alert.alert_id,
                "transaction_id": alert.transaction_id,
                "user_id": alert.user_id,
                "risk_score": alert.risk_score,
                "risk_level": alert.risk_level.value,
                "fraud_types": [ft.value for ft in alert.fraud_types],
                "confidence": alert.confidence,
                "timestamp": alert.timestamp.isoformat(),
                "features_used": alert.features_used,
                "model_version": alert.model_version,
                "explanation": alert.explanation,
                "recommended_actions": alert.recommended_actions,
            }
            alerts_data.append(alert_data)
        return (
            jsonify(
                {
                    "success": True,
                    "alerts": alerts_data,
                    "total_processed": len(transactions),
                }
            ),
            200,
        )
    except FraudDetectionError as e:
        return (jsonify({"success": False, "error": str(e)}), 400)
    except Exception as e:
        logger.error(f"Batch fraud detection failed: {str(e)}")
        return (jsonify({"success": False, "error": str(e)}), 500)


@fraud_detection_bp.route("/model/train", methods=["POST"])
@cross_origin()
def train_model() -> object:
    """Train the fraud detection model"""
    try:
        data = request.get_json()
        if "training_data" not in data:
            return (
                jsonify(
                    {"success": False, "error": "Missing required field: training_data"}
                ),
                400,
            )
        training_df = pd.DataFrame(data["training_data"])
        labels = None
        if "labels" in data and data["labels"]:
            labels = pd.Series(data["labels"])
        validation_data = None
        if "validation_data" in data and data["validation_data"]:
            val_df = pd.DataFrame(data["validation_data"])
            val_labels = pd.Series(data.get("validation_labels", []))
            validation_data = (val_df, val_labels)
        fraud_service = get_fraud_service()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        training_results = loop.run_until_complete(
            fraud_service.train_model(training_df, labels, validation_data)
        )
        loop.close()
        return (jsonify({"success": True, "training_results": training_results}), 200)
    except FraudDetectionError as e:
        return (jsonify({"success": False, "error": str(e)}), 400)
    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")
        return (jsonify({"success": False, "error": str(e)}), 500)


@fraud_detection_bp.route("/model/status", methods=["GET"])
@cross_origin()
def get_model_status() -> "flask.Response":
    """Get fraud detection model status"""
    try:
        fraud_service = get_fraud_service()
        status = fraud_service.get_model_status()
        if status.get("training_timestamp"):
            status["training_timestamp"] = status["training_timestamp"].isoformat()
        if status.get("performance_metrics", {}).get("last_retrain"):
            status["performance_metrics"]["last_retrain"] = status[
                "performance_metrics"
            ]["last_retrain"].isoformat()
        return (jsonify({"success": True, "model_status": status}), 200)
    except Exception as e:
        logger.error(f"Failed to get model status: {str(e)}")
        return (jsonify({"success": False, "error": str(e)}), 500)


@fraud_detection_bp.route("/alerts", methods=["GET"])
@cross_origin()
def get_recent_alerts() -> "flask.Response":
    """Get recent fraud alerts"""
    try:
        hours = request.args.get("hours", 24, type=int)
        risk_levels = request.args.getlist("risk_levels")
        risk_level_enums = []
        for level in risk_levels:
            try:
                risk_level_enums.append(RiskLevel(level))
            except ValueError:
                return (
                    jsonify(
                        {"success": False, "error": f"Invalid risk level: {level}"}
                    ),
                    400,
                )
        fraud_service = get_fraud_service()
        alerts = fraud_service.get_recent_alerts(
            hours=hours, risk_levels=risk_level_enums if risk_level_enums else None
        )
        alerts_data = []
        for alert in alerts:
            alert_data = {
                "alert_id": alert.alert_id,
                "transaction_id": alert.transaction_id,
                "user_id": alert.user_id,
                "risk_score": alert.risk_score,
                "risk_level": alert.risk_level.value,
                "fraud_types": [ft.value for ft in alert.fraud_types],
                "confidence": alert.confidence,
                "timestamp": alert.timestamp.isoformat(),
                "recommended_actions": alert.recommended_actions,
            }
            alerts_data.append(alert_data)
        return (
            jsonify(
                {
                    "success": True,
                    "alerts": alerts_data,
                    "total_alerts": len(alerts_data),
                    "hours_analyzed": hours,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to get alerts: {str(e)}")
        return (jsonify({"success": False, "error": str(e)}), 500)


@fraud_detection_bp.route("/statistics", methods=["GET"])
@cross_origin()
def get_fraud_statistics() -> "flask.Response":
    """Get fraud detection statistics"""
    try:
        hours = request.args.get("hours", 24, type=int)
        fraud_service = get_fraud_service()
        statistics = fraud_service.get_fraud_statistics(hours)
        return (
            jsonify(
                {"success": True, "statistics": statistics, "hours_analyzed": hours}
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        return (jsonify({"success": False, "error": str(e)}), 500)


@fraud_detection_bp.route("/feedback", methods=["POST"])
@cross_origin()
def submit_feedback() -> object:
    """Submit feedback on fraud detection results"""
    try:
        data = request.get_json()
        required_fields = ["transaction_id", "is_fraud"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify(
                        {"success": False, "error": f"Missing required field: {field}"}
                    ),
                    400,
                )
        transaction_id = data["transaction_id"]
        is_fraud = bool(data["is_fraud"])
        feedback_type = data.get("feedback_type", "manual_review")
        fraud_service = get_fraud_service()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            fraud_service.update_model_feedback(transaction_id, is_fraud, feedback_type)
        )
        loop.close()
        return (
            jsonify({"success": True, "message": "Feedback submitted successfully"}),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to submit feedback: {str(e)}")
        return (jsonify({"success": False, "error": str(e)}), 500)


@fraud_detection_bp.route("/model/retrain/check", methods=["GET"])
@cross_origin()
def check_retrain_needed() -> None:
    """Check if model retraining is needed"""
    try:
        fraud_service = get_fraud_service()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        retrain_needed = loop.run_until_complete(fraud_service.check_retrain_needed())
        loop.close()
        return (
            jsonify(
                {
                    "success": True,
                    "retrain_needed": retrain_needed,
                    "auto_retrain_enabled": fraud_service.auto_retrain,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Failed to check retrain status: {str(e)}")
        return (jsonify({"success": False, "error": str(e)}), 500)


@fraud_detection_bp.route("/health", methods=["GET"])
@cross_origin()
def health_check() -> "flask.Response":
    """Health check endpoint for fraud detection service"""
    try:
        fraud_service = get_fraud_service()
        status = fraud_service.get_model_status()
        is_healthy = (
            status.get("model_initialized", False)
            and status.get("model_trained", False)
            and status.get("real_time_detector_ready", False)
        )
        return (
            jsonify(
                {
                    "success": True,
                    "health_status": "healthy" if is_healthy else "degraded",
                    "model_ready": is_healthy,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return (jsonify({"success": False, "error": str(e)}), 500)


@fraud_detection_bp.errorhandler(FraudDetectionError)
def handle_fraud_detection_error(e: Any) -> "flask.Response":
    return (
        jsonify(
            {"success": False, "error": "Fraud detection error", "details": str(e)}
        ),
        400,
    )
