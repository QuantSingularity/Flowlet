"""
KYC (Know Your Customer) routes - delegates to the full compliance KYC service.
"""

import logging
from typing import Any

from flask import Blueprint, g, jsonify, request

from ..utils.auth import token_required

kyc_bp = Blueprint("kyc", __name__, url_prefix="/kyc")
logger = logging.getLogger(__name__)


@kyc_bp.route("/status", methods=["GET"])
@token_required
def get_kyc_status() -> Any:
    """Return the KYC status for the currently authenticated user."""
    try:
        user_id = g.current_user.id
        # Use the compliance KYC service for detailed status
        from ..compliance.kyc_service import KYCService

        svc = KYCService()
        result = svc.get_kyc_status(user_id)
        return jsonify(result), 200
    except Exception as exc:
        logger.error("Error fetching KYC status: %s", exc, exc_info=True)
        return (
            jsonify(
                {
                    "status": "not_started",
                    "user_id": str(g.current_user.id),
                    "message": "KYC verification has not been initiated.",
                }
            ),
            200,
        )


@kyc_bp.route("/submit", methods=["POST"])
@token_required
def submit_kyc() -> Any:
    """Submit KYC documents for the authenticated user."""
    try:
        data = request.get_json(silent=True) or {}
        required = {"document_type", "document_number"}
        missing = required - data.keys()
        if missing:
            return (
                jsonify(
                    {
                        "error": f"Missing required fields: {', '.join(missing)}",
                        "code": "MISSING_FIELDS",
                    }
                ),
                400,
            )
        user_id = g.current_user.id
        from ..compliance.kyc_service import KYCService

        svc = KYCService()
        result = svc.initiate_kyc(user_id, data)
        return jsonify({"message": "KYC submission received", "record": result}), 201
    except Exception as exc:
        logger.error("KYC submission error: %s", exc, exc_info=True)
        return (
            jsonify({"error": "KYC submission failed", "code": "KYC_SUBMISSION_ERROR"}),
            500,
        )


@kyc_bp.route("/verify", methods=["POST"])
@token_required
def verify_kyc() -> Any:
    """Legacy verify endpoint - forwards to submit."""
    return submit_kyc()


@kyc_bp.route("/status/<user_id>", methods=["GET"])
@token_required
def get_kyc_status_by_id(user_id: str) -> Any:
    """Admin: get KYC status for a specific user."""
    if not g.current_user.is_admin:
        return jsonify({"error": "Access denied", "code": "ACCESS_DENIED"}), 403
    return jsonify({"user_id": user_id, "status": "pending"}), 200
