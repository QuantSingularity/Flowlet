import os
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import FrozenSet, Optional

_TRUE = {"1", "true", "yes", "on"}
_DEFAULT_HIGH_RISK_COUNTRIES = ("KP", "IR", "MM", "SY", "CU")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_set(name: str, default: tuple) -> FrozenSet[str]:
    raw = os.environ.get(name)
    if raw is None:
        return frozenset(default)
    return frozenset(item.strip().upper() for item in raw.split(",") if item.strip())


def _detect_environment() -> str:
    explicit = os.environ.get("ML_ENVIRONMENT")
    if explicit:
        return explicit.strip().lower()
    flask_env = os.environ.get("FLASK_CONFIG") or os.environ.get("FLASK_ENV") or ""
    return flask_env.strip().lower() or "development"


@dataclass(frozen=True)
class MLSettings:
    environment: str = "development"
    enabled: bool = True
    model_dir: Path = field(
        default_factory=lambda: Path(tempfile.gettempdir()) / "flowlet_ml_models"
    )
    signing_key: Optional[str] = None
    persist_models: bool = True
    keep_versions: int = 5
    bootstrap_on_start: bool = True
    bootstrap_samples: int = 6000
    bootstrap_fraud_rate: float = 0.06
    random_state: int = 42
    medium_threshold: float = 0.3
    high_threshold: float = 0.6
    critical_threshold: float = 0.8
    auto_retrain: bool = True
    retrain_interval_days: int = 30
    min_feedback_samples: int = 200
    drift_psi_threshold: float = 0.25
    min_promotion_gain: float = -0.005
    fail_open: bool = True
    enforce_in_payments: bool = True
    block_in_payments: bool = True
    redis_url: Optional[str] = None
    history_window_days: int = 90
    max_history_per_user: int = 500
    alert_retention: int = 10000
    feature_cache_size: int = 50000
    high_risk_countries: FrozenSet[str] = frozenset(_DEFAULT_HIGH_RISK_COUNTRIES)
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.environment in {"production", "prod"}

    @classmethod
    def from_env(cls) -> "MLSettings":
        environment = _detect_environment()
        production = environment in {"production", "prod"}
        signing_key = os.environ.get("ML_ARTIFACT_SIGNING_KEY") or os.environ.get(
            "SECRET_KEY"
        )
        model_dir = Path(
            os.environ.get("ML_MODEL_DIR")
            or Path(tempfile.gettempdir()) / "flowlet_ml_models"
        )
        return cls(
            environment=environment,
            enabled=_env_bool("ML_ENABLED", _env_bool("FRAUD_DETECTION_ENABLED", True)),
            model_dir=model_dir,
            signing_key=signing_key,
            persist_models=_env_bool("ML_PERSIST_MODELS", True),
            keep_versions=max(1, _env_int("ML_KEEP_VERSIONS", 5)),
            bootstrap_on_start=_env_bool("ML_BOOTSTRAP_ON_START", not production),
            bootstrap_samples=max(500, _env_int("ML_BOOTSTRAP_SAMPLES", 6000)),
            bootstrap_fraud_rate=_env_float("ML_BOOTSTRAP_FRAUD_RATE", 0.06),
            random_state=_env_int("ML_RANDOM_STATE", 42),
            medium_threshold=_env_float("ML_MEDIUM_THRESHOLD", 0.3),
            high_threshold=_env_float("ML_HIGH_THRESHOLD", 0.6),
            critical_threshold=_env_float("ML_CRITICAL_THRESHOLD", 0.8),
            auto_retrain=_env_bool("ML_AUTO_RETRAIN", True),
            retrain_interval_days=max(1, _env_int("ML_RETRAIN_INTERVAL_DAYS", 30)),
            min_feedback_samples=max(10, _env_int("ML_MIN_FEEDBACK_SAMPLES", 200)),
            drift_psi_threshold=_env_float("ML_DRIFT_PSI_THRESHOLD", 0.25),
            min_promotion_gain=_env_float("ML_MIN_PROMOTION_GAIN", -0.005),
            fail_open=_env_bool("ML_FAIL_OPEN", True),
            enforce_in_payments=_env_bool("ML_ENFORCE_IN_PAYMENTS", True),
            block_in_payments=_env_bool("ML_BLOCK_IN_PAYMENTS", True),
            redis_url=os.environ.get("ML_REDIS_URL") or None,
            history_window_days=max(1, _env_int("ML_HISTORY_WINDOW_DAYS", 90)),
            max_history_per_user=max(10, _env_int("ML_MAX_HISTORY_PER_USER", 500)),
            alert_retention=max(100, _env_int("ML_ALERT_RETENTION", 10000)),
            feature_cache_size=max(100, _env_int("ML_FEATURE_CACHE_SIZE", 50000)),
            high_risk_countries=_env_set(
                "ML_HIGH_RISK_COUNTRIES", _DEFAULT_HIGH_RISK_COUNTRIES
            ),
            log_level=os.environ.get("ML_LOG_LEVEL", "INFO").upper(),
        )


_lock = threading.Lock()
_cached: Optional[MLSettings] = None


def get_settings() -> MLSettings:
    global _cached
    if _cached is None:
        with _lock:
            if _cached is None:
                _cached = MLSettings.from_env()
    return _cached


def reload_settings() -> MLSettings:
    global _cached
    with _lock:
        _cached = MLSettings.from_env()
    return _cached
