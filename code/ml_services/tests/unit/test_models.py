import numpy as np
import pytest
from ml_services.core import FraudDetectionError, ModelNotTrainedError, RiskLevel
from ml_services.fraud_detection import (
    AutoencoderModel,
    EnsembleFraudModel,
    IsolationForestModel,
    LightGBMFraudModel,
    NeuralNetworkFraudModel,
    OneClassSVMModel,
    RandomForestFraudModel,
    XGBoostFraudModel,
)
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


@pytest.fixture(scope="module")
def split(labeled_data):
    features, labels = labeled_data
    return train_test_split(
        features, labels, test_size=0.3, stratify=labels, random_state=2
    )


@pytest.mark.parametrize(
    "model_class,config",
    [
        (RandomForestFraudModel, {"n_estimators": 40}),
        (XGBoostFraudModel, {"n_estimators": 40}),
        (LightGBMFraudModel, {"n_estimators": 40}),
        (NeuralNetworkFraudModel, {"max_iter": 40}),
    ],
)
def test_supervised_models_learn(model_class, config, split):
    x_train, x_test, y_train, y_test = split
    model = model_class(config)
    model.train(x_train, y_train)
    scores = model.predict(x_test)
    assert scores.shape == (len(x_test),)
    assert scores.min() >= 0 and scores.max() <= 1
    assert roc_auc_score(y_test, scores) > 0.9
    importance = model.get_feature_importance()
    assert abs(sum(importance.values()) - 1.0) < 1e-6
    assert model.local_contributions(x_test.iloc[[0]])


@pytest.mark.parametrize(
    "model_class,config",
    [
        (IsolationForestModel, {"n_estimators": 40}),
        (OneClassSVMModel, {"max_training_samples": 800}),
        (AutoencoderModel, {"max_iter": 40}),
    ],
)
def test_anomaly_models_separate_fraud(model_class, config, split):
    x_train, x_test, y_train, y_test = split
    model = model_class(config)
    model.train(x_train, y_train)
    scores = model.predict(x_test)
    assert scores.min() >= 0 and scores.max() <= 1
    assert roc_auc_score(y_test, scores) > 0.7


def test_anomaly_scores_are_independent_of_batch(split):
    x_train, x_test, y_train, _ = split
    model = IsolationForestModel({"n_estimators": 40})
    model.train(x_train, y_train)
    batch = model.predict(x_test.iloc[:20])
    single = np.array([model.predict(x_test.iloc[[i]])[0] for i in range(20)])
    assert np.allclose(batch, single)


def test_untrained_model_raises():
    with pytest.raises(ModelNotTrainedError):
        IsolationForestModel({}).predict({"amount": 1})


def test_supervised_training_requires_both_classes(split):
    x_train, _, y_train, _ = split
    with pytest.raises(FraudDetectionError):
        RandomForestFraudModel({}).train(x_train, np.zeros(len(x_train)))
    with pytest.raises(FraudDetectionError):
        RandomForestFraudModel({}).train(x_train, None)


def test_risk_level_calculation():
    model = IsolationForestModel({})
    assert model.calculate_risk_level(0.1) == RiskLevel.LOW
    assert model.calculate_risk_level(0.4) == RiskLevel.MEDIUM
    assert model.calculate_risk_level(0.7) == RiskLevel.HIGH
    assert model.calculate_risk_level(0.9) == RiskLevel.CRITICAL


def test_ensemble_stacking_beats_chance_and_exposes_status(
    trained_ensemble, labeled_data
):
    features, labels = labeled_data
    scores = trained_ensemble.predict(features)
    assert roc_auc_score(labels, scores) > 0.95
    status = trained_ensemble.status()
    assert status["stacking_active"] is True
    assert set(status["members"]) >= {"random_forest", "isolation_forest"}


@pytest.mark.parametrize("strategy", ["weighted", "average"])
def test_ensemble_alternative_strategies(strategy, fast_config, split):
    x_train, x_test, y_train, y_test = split
    fast_config["voting_strategy"] = strategy
    fast_config["models"] = {
        "isolation_forest": {"n_estimators": 30},
        "random_forest": {"n_estimators": 30},
    }
    model = EnsembleFraudModel(fast_config)
    model.train(x_train, y_train)
    assert model.voting_strategy == strategy
    assert roc_auc_score(y_test, model.predict(x_test)) > 0.9


def test_ensemble_without_labels_uses_anomaly_members_only(fast_config, split):
    x_train, x_test, _, _ = split
    fast_config["voting_strategy"] = "stacking"
    model = EnsembleFraudModel(fast_config)
    model.train(x_train)
    assert model.voting_strategy == "weighted"
    assert "random_forest" in model.skipped
    assert model.predict(x_test.iloc[:5]).shape == (5,)


def test_ensemble_fails_when_no_member_trains():
    model = EnsembleFraudModel({"models": {"random_forest": {}}})
    import pandas as pd

    with pytest.raises(FraudDetectionError):
        model.train(pd.DataFrame({"amount": [1.0, 2.0, 3.0]}))


def test_ensemble_handles_unseen_columns(trained_ensemble):
    score = trained_ensemble.predict({"amount": 50, "not_a_feature": 3})
    assert 0 <= score[0] <= 1


def test_ensemble_artifact_roundtrip(trained_ensemble, tmp_path, labeled_data):
    from ml_services.core import ModelRegistry

    registry = ModelRegistry(tmp_path, "k")
    registry.save("ens", trained_ensemble)
    loaded, _ = registry.load("ens")
    features, _ = labeled_data
    assert np.allclose(
        loaded.predict(features.head(10)), trained_ensemble.predict(features.head(10))
    )
