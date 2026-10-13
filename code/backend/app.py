import logging
import os
import sys

# Ensure code/ root is in sys.path so ml_services.* imports resolve at runtime
_backend_dir = os.path.dirname(os.path.abspath(__file__))
_code_root = os.path.dirname(_backend_dir)
if _code_root not in sys.path:
    sys.path.insert(0, _code_root)
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from src.config.settings import config
from src.models import db
from src.routes import api_bp
from src.utils.error_handlers import register_error_handlers


def create_app(config_name: Optional[str] = None) -> Flask:
    """Create and configure the Flask application."""
    static_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "web-frontend", "dist"
    )
    if not os.path.isdir(static_dir):
        static_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "src", "static"
        )
    app = Flask(__name__, static_folder=static_dir, static_url_path="")

    from flask.json.provider import DefaultJSONProvider

    class CustomJSONProvider(DefaultJSONProvider):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    app.json = CustomJSONProvider(app)

    resolved_config = config_name or os.environ.get("FLASK_CONFIG", "default")
    app.config.from_object(config[resolved_config])
    if hasattr(config[resolved_config], "validate_config"):
        config[resolved_config].validate_config()

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri and db_uri.startswith("sqlite:///"):
        db_file = db_uri.split("sqlite:///", 1)[1]
        if db_file and db_file != ":memory:":
            db_dir = os.path.dirname(os.path.abspath(db_file))
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

    db.init_app(app)
    Migrate(app, db)
    Limiter(key_func=get_remote_address, app=app)

    cors_origins = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5000"
    ).split(",")
    CORS(app, resources={"/*": {"origins": cors_origins}}, supports_credentials=True)

    logging.basicConfig(level=logging.INFO)
    logger = app.logger
    logger.info("Starting Flask application")

    app.register_blueprint(api_bp)

    if not app.config.get("TESTING"):
        from src.services.ml_gateway import warm_up_models

        warm_up_models()

    @app.route("/health")
    def health_check() -> Any:
        """Health check endpoint."""
        from sqlalchemy import text
        from src.services.ml_gateway import get_ml, ml_enabled

        database = "ok"
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            database = "error"
        ml_status = "disabled"
        if ml_enabled():
            try:
                ml_status = get_ml().health()["status"]
            except Exception:
                ml_status = "error"
        overall = "healthy" if database == "ok" else "unhealthy"
        return (
            jsonify(
                {
                    "status": overall,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "version": "2.0.0",
                    "services": {"database": database, "api": "ok", "ml": ml_status},
                }
            ),
            200 if overall == "healthy" else 503,
        )

    @app.route("/api/v1/info")
    def api_info() -> Any:
        """API info endpoint."""
        resp = jsonify(
            {
                "api_name": "Flowlet Financial Backend - Enhanced MVP",
                "version": "2.0.0",
                "api_version": "2.0.0",
                "endpoints": [
                    "/api/v1/auth",
                    "/api/v1/users",
                    "/api/v1/wallets",
                    "/api/v1/payments",
                    "/api/v1/cards",
                    "/api/v1/transactions",
                    "/api/v1/analytics",
                    "/api/v1/compliance",
                    "/api/v1/fraud",
                    "/api/v1/ai",
                    "/api/v1/kyc",
                ],
                "security_features": [
                    "JWT Authentication",
                    "Rate Limiting",
                    "Input Validation",
                    "AML Monitoring",
                    "Fraud Detection",
                ],
                "supported_currencies": ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"],
            }
        )
        # Security headers are applied globally by the after_request handler.
        return resp

    @app.route("/api/v1/docs")
    def api_docs() -> Any:
        """API documentation endpoint."""
        resp = jsonify(
            {
                "api_name": "Flowlet Financial Backend - Enhanced MVP",
                "api_version": "2.0.0",
                "endpoints": [
                    "/api/v1/auth",
                    "/api/v1/users",
                    "/api/v1/accounts",
                    "/api/v1/payments",
                    "/api/v1/cards",
                    "/api/v1/transactions",
                    "/api/v1/analytics",
                    "/api/v1/compliance",
                    "/api/v1/fraud",
                    "/api/v1/ai",
                    "/api/v1/kyc",
                    "/api/v1/currency",
                ],
                "security_features": [
                    "JWT Authentication",
                    "Rate Limiting",
                    "Input Validation",
                    "AML Monitoring",
                    "Fraud Detection",
                ],
                "supported_currencies": ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"],
            }
        )
        return resp

    @app.route("/")
    def serve_web_frontend() -> Any:
        """Serve the React web-frontend index page."""
        try:
            return send_from_directory(app.static_folder, "index.html")
        except Exception:
            return jsonify({"status": "ok", "message": "Flowlet API is running"}), 200

    @app.route("/<path:path>")
    def serve_static_files(path) -> Any:
        """Serve static files or fallback to index.html for SPA routing."""
        try:
            return send_from_directory(app.static_folder, path)
        except Exception:
            try:
                return send_from_directory(app.static_folder, "index.html")
            except Exception:
                return (
                    jsonify(
                        {
                            "error": "Not Found",
                            "code": "NOT_FOUND",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    ),
                    404,
                )

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
        return response

    register_error_handlers(app)

    @app.errorhandler(404)
    def not_found_handler(e: Exception) -> Any:
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "code": "NOT_FOUND",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            404,
        )

    @app.errorhandler(400)
    def bad_request_handler(e: Exception) -> Any:
        return (
            jsonify({"status": "error", "message": "Bad request", "error": str(e)}),
            400,
        )

    @app.errorhandler(Exception)
    def handle_exception(e: Exception) -> Any:
        app.logger.error("Unhandled Exception", exc_info=True)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "An internal server error occurred. Please try again later.",
                }
            ),
            500,
        )

    with app.app_context():
        db_uri_local = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_uri_local and db_uri_local != "sqlite:///:memory:":
            try:
                db.create_all()
                logger.info("Database initialized successfully")
            except Exception as exc:
                logger.warning(f"Database initialization skipped: {exc}")

    return app
