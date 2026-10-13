import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-testing-only")
os.environ.setdefault("ML_BOOTSTRAP_ON_START", "false")
os.environ.setdefault("ML_PERSIST_MODELS", "false")

code_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if code_root not in sys.path:
    sys.path.insert(0, code_root)

import pytest
from ml_services.config import MLSettings
from ml_services.data import generate_labeled_features


@pytest.fixture(scope="session")
def labeled_data():
    return generate_labeled_features(2500, 0.08, 11)


@pytest.fixture
def settings(tmp_path):
    return MLSettings(
        model_dir=Path(tempfile.mkdtemp(dir=tmp_path)),
        signing_key="unit-test-key",
        bootstrap_on_start=False,
        bootstrap_samples=1500,
    )


FAST_MODELS = {
    "voting_strategy": "stacking",
    "cv_folds": 3,
    "random_state": 3,
    "models": {
        "isolation_forest": {"n_estimators": 40},
        "autoencoder": {"max_iter": 30},
        "random_forest": {"n_estimators": 40},
        "xgboost": {"n_estimators": 40},
        "lightgbm": {"n_estimators": 40},
        "neural_network": {"max_iter": 30},
    },
}


@pytest.fixture
def fast_config():
    import copy

    return copy.deepcopy(FAST_MODELS)


@pytest.fixture(scope="session")
def trained_ensemble(labeled_data):
    import copy

    from ml_services.fraud_detection.models import EnsembleFraudModel

    features, labels = labeled_data
    model = EnsembleFraudModel(copy.deepcopy(FAST_MODELS))
    model.train(features, labels)
    return model
