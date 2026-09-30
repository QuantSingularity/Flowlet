import os

from dotenv import load_dotenv

from .security import SecurityConfig

load_dotenv()


def _get_engine_options():
    """Return SQLAlchemy engine options compatible with the configured database."""
    db_url = os.environ.get("DATABASE_URL", "sqlite")
    if "sqlite" in db_url:
        return {"pool_pre_ping": True}
    return {
        "pool_size": 20,
        "max_overflow": 30,
        "pool_timeout": 30,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }


class Config:
    """Base configuration class with security-focused defaults"""

    _SECRET_KEY_DEFAULT = "dev-secret-key-change-in-production"  # noqa: S105
    SECRET_KEY = os.environ.get("SECRET_KEY") or _SECRET_KEY_DEFAULT
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "app.db")
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or f"sqlite:///{DEFAULT_DB_PATH}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _get_engine_options()
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
    JWT_SECRET_KEY = (
        os.environ.get("JWT_SECRET_KEY")
        or "dev-jwt-secret-change-in-production"  # noqa: S105
    )
    JWT_ACCESS_TOKEN_EXPIRES = SecurityConfig.JWT_ACCESS_TOKEN_EXPIRES
    JWT_REFRESH_TOKEN_EXPIRES = SecurityConfig.JWT_REFRESH_TOKEN_EXPIRES
    JWT_ALGORITHM = SecurityConfig.JWT_ALGORITHM
    PASSWORD_MIN_LENGTH = SecurityConfig.PASSWORD_MIN_LENGTH
    PASSWORD_REQUIRE_UPPERCASE = SecurityConfig.PASSWORD_REQUIRE_UPPERCASE
    PASSWORD_REQUIRE_LOWERCASE = SecurityConfig.PASSWORD_REQUIRE_LOWERCASE
    PASSWORD_REQUIRE_NUMBERS = SecurityConfig.PASSWORD_REQUIRE_NUMBERS
    PASSWORD_REQUIRE_SPECIAL_CHARS = SecurityConfig.PASSWORD_REQUIRE_SPECIAL_CHARS
    PASSWORD_MAX_AGE_DAYS = 90
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = SecurityConfig.DEFAULT_RATE_LIMIT
    RATELIMIT_HEADERS_ENABLED = True
    SESSION_TIMEOUT_MINUTES = 30
    SESSION_COOKIE_SECURE = SecurityConfig.SESSION_COOKIE_SECURE
    SESSION_COOKIE_HTTPONLY = SecurityConfig.SESSION_COOKIE_HTTPONLY
    SESSION_COOKIE_SAMESITE = SecurityConfig.SESSION_COOKIE_SAMESITE
    CORS_ORIGINS = SecurityConfig.CORS_ORIGINS
    ENCRYPTION_KEY = (
        os.environ.get("ENCRYPTION_KEY") or "dev-encryption-key-32byteslong!!"
    )
    AUDIT_LOG_RETENTION_DAYS = SecurityConfig.AUDIT_LOG_RETENTION_DAYS
    MAX_CONTENT_LENGTH = SecurityConfig.MAX_CONTENT_LENGTH
    API_TITLE = "Flowlet Financial Backend"
    API_VERSION = "v1.0.0"
    PCI_DSS_COMPLIANCE = True
    SOX_COMPLIANCE = True
    GDPR_COMPLIANCE = True
    ENABLE_METRICS = True
    ENABLE_HEALTH_CHECKS = True
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    FRAUD_DETECTION_ENABLED = True
    MAX_DAILY_TRANSACTION_AMOUNT = 50000.0
    MAX_SINGLE_TRANSACTION_AMOUNT = 10000.0
    SUSPICIOUS_ACTIVITY_THRESHOLD = 5
    KYC_VERIFICATION_REQUIRED = True
    AML_MONITORING_ENABLED = True
    SANCTIONS_LIST_CHECK_ENABLED = True
    CARD_ENCRYPTION_ENABLED = True
    CARD_TOKENIZATION_ENABLED = True
    CARD_CVV_STORAGE_PROHIBITED = True
    DEFAULT_DAILY_LIMIT = 5000.0
    DEFAULT_MONTHLY_LIMIT = 50000.0
    DEFAULT_YEARLY_LIMIT = 500000.0
    SUPPORTED_CURRENCIES = [
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "CAD",
        "AUD",
        "CHF",
        "CNY",
        "SEK",
        "NZD",
        "MXN",
        "SGD",
        "HKD",
        "NOK",
        "TRY",
        "ZAR",
        "BRL",
        "INR",
        "KRW",
        "PLN",
    ]
    DEFAULT_CURRENCY = "USD"
    BACKUP_ENABLED = True
    BACKUP_RETENTION_DAYS = 90

    @staticmethod
    def validate_config() -> None:
        """Validate critical configuration settings"""
        return True


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    def __init__(self) -> None:
        import logging

        _log = logging.getLogger(__name__)
        if self.SECRET_KEY == self._SECRET_KEY_DEFAULT:
            _log.warning(
                "⚠️  Using default SECRET_KEY - set SECRET_KEY env var before deploying."
            )
        if self.JWT_SECRET_KEY == "dev-jwt-secret-change-in-production":
            _log.warning(
                "⚠️  Using default JWT_SECRET_KEY - set JWT_SECRET_KEY env var before deploying."
            )


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key-for-testing-only")
    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY", "test-jwt-secret-for-testing-only"
    )
    ENCRYPTION_KEY = "test-encryption-key-32byteslong!!"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False

    @staticmethod
    def validate_config() -> None:
        """Skip validation in testing"""
        return True


class ProductionConfig(Config):
    """Production configuration with enhanced security"""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    RATELIMIT_DEFAULT = "500 per hour"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 50,
        "max_overflow": 100,
        "pool_timeout": 30,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    @staticmethod
    def validate_config() -> None:
        """Validate critical configuration in production"""
        errors = []
        secret = os.environ.get("SECRET_KEY", "")
        if not secret or secret.startswith("dev-"):
            errors.append(
                "SECRET_KEY must be set to a strong random value in production."
            )
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        return True


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
