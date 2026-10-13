from typing import Any, Dict, Optional, Tuple

from flask import g, jsonify, request

from ..models.database import db
from ..models.user import User


def error_response(message: str, code: str, status: int) -> Tuple[Any, int]:
    return jsonify({"error": message, "code": code}), status


def json_body(
    required: Optional[Tuple[str, ...]] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[Any, int]]]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, error_response("JSON object body is required", "INVALID_BODY", 400)
    for field in required or ():
        if field not in data or data[field] in (None, ""):
            return None, error_response(
                f"Missing required field: {field}", "MISSING_FIELD", 400
            )
    return data, None


def is_admin() -> bool:
    user = getattr(g, "current_user", None)
    return bool(user and user.is_admin)


def resolve_target_user(
    requested_id: Optional[str],
) -> Tuple[Optional[User], Optional[Tuple[Any, int]]]:
    current = g.current_user
    if requested_id and str(requested_id) != str(current.id):
        if not is_admin():
            return None, error_response("Access denied", "FORBIDDEN", 403)
        target = db.session.get(User, str(requested_id))
        if target is None:
            return None, error_response("User not found", "USER_NOT_FOUND", 404)
        return target, None
    return current, None


def int_arg(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(request.args.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, value))
