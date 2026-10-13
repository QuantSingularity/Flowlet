"""Authentication utilities"""

import os
from functools import wraps
from typing import Any

import jwt
from flask import current_app, g, jsonify, request

from ..models.database import db
from ..models.user import User


def _jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY") or current_app.config.get(
        "JWT_SECRET_KEY"
    )
    if not secret:
        raise RuntimeError("JWT secret is not configured")
    return str(secret)


def token_required(f: Any) -> object:
    """Decorator to require valid JWT token and populate g.current_user"""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> object:
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing"}), 401

        try:
            if token.startswith("Bearer "):
                token = token[7:]
            secret = _jwt_secret()
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            current_user = db.session.get(User, payload.get("user_id"))
            if not current_user:
                return jsonify({"message": "User not found"}), 401
            if not current_user.is_active:
                return jsonify({"message": "User account is inactive"}), 401
            g.current_user = current_user
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token is invalid"}), 401
        except Exception:
            return jsonify({"message": "Token is invalid"}), 401

        return f(*args, **kwargs)

    return decorated


def admin_required(f: Any) -> object:
    """Decorator to require admin role"""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> object:
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing"}), 401

        try:
            if token.startswith("Bearer "):
                token = token[7:]
            secret = _jwt_secret()
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            current_user = db.session.get(User, payload.get("user_id"))
            if not current_user:
                return jsonify({"message": "User not found"}), 401
            if not current_user.is_active:
                return jsonify({"message": "User account is inactive"}), 401
            if not current_user.is_admin:
                return jsonify({"message": "Admin access required"}), 403
            g.current_user = current_user
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token is invalid"}), 401
        except Exception:
            return jsonify({"message": "Token is invalid"}), 401

        return f(*args, **kwargs)

    return decorated


# Re-export from password_security for backward compatibility
from ..security.password_security import check_password  # noqa: F401
