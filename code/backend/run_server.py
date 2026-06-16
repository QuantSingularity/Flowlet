"""
Flowlet Financial Backend - Application Entry Point
Used by both Gunicorn (production) and the development server.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _backend_dir)
# code/ root – resolves ml_services.* imports
_code_root = os.path.dirname(_backend_dir)
if _code_root not in sys.path:
    sys.path.insert(0, _code_root)

# Set safe defaults for required environment variables
os.environ.setdefault("SECRET_KEY", "dev-secret-key-change-in-production-32chars")
os.environ.setdefault("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-32chars")
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("FLASK_CONFIG", "development")
os.environ.setdefault("OPENAI_API_KEY", "sk-placeholder")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_placeholder")

from app import create_app

app = create_app()

# Expose Celery instance if available
try:
    from celery import Celery

    celery = Celery(app.name)
    celery.conf.update(
        broker_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        result_backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    )
except ImportError:
    celery = None

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"

    print("=" * 60)
    print("  Flowlet Financial Backend")
    print("=" * 60)
    print(f"  Blueprints  : {len(app.blueprints)}")
    print(f"  Database    : {app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')[:60]}")
    print(f"  Debug       : {debug}")
    print(f"  Listening   : http://{host}:{port}")
    print("=" * 60)

    app.run(host=host, port=port, debug=debug)
