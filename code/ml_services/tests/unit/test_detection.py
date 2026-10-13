import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from ml_services.core import FraudAction, FraudDetectionError, FraudType, RiskLevel
from ml_services.features import FeatureEngineer
from ml_services.fraud_detection import (
    FraudDetectionService,
    FraudExplainer,
    RealTimeFraudDetector,
    RuleEngine,
)


def _history(count=30):
    now = datetime.now(timezone.utc)
    return [
        {
            "timestamp": (now - timedelta(hours=6 * (index + 1))).isoformat(),
            "amount": 30.0,
            "location_country": "US",
            "device_fingerprint": "known",
            "merchant_category": "grocery",
        }
        for index in range(count)
    ]


def test_rules_flag_sanctioned_country_and_structuring():
    engineer = FeatureEngineer()
    features = engineer.extract_transaction_features(
        {"amount": 9500, "location_country": "KP", "user_id": "u"}, _history()
    )
    score, hits = RuleEngine().evaluate(features)
    names = {hit.name for hit in hits}
    assert {"high_risk_country", "structuring_pattern"} <= names
    assert score > 0.7


def test_rules_quiet_for_normal_transaction():
    features = FeatureEngineer().extract_transaction_features(
        {
            "amount": 31,
            "location_country": "US",
            "device_fingerprint": "known",
            "merchant_category": "grocery",
        },
        _history(),
    )
    score, hits = RuleEngine().evaluate(features)
    assert hits == [] and score == 0.0


def test_rapid_country_change_rule():
    now = datetime.now(timezone.utc)
    history = [
        {
            "timestamp": (now - timedelta(minutes=20)).isoformat(),
            "amount": 20,
            "location_country": "US",
        }
    ]
    features = FeatureEngineer().extract_transaction_features(
        {"amount": 25, "location_country": "FR"}, history
    )
    _, hits = RuleEngine().evaluate(features)
    assert "rapid_country_change" in {hit.name for hit in hits}


def test_detector_rules_only_mode_high_amount():
    alert = RealTimeFraudDetector().detect_fraud({"amount": 50000, "user_id": "u1"})
    assert alert.risk_score >= 0.3
    assert alert.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert alert.metadata["mode"] == "rules_only"
    assert FraudType.PAYMENT_FRAUD in alert.fraud_types
    assert alert.explanation["summary"]


def test_detector_low_risk_transaction():
    alert = RealTimeFraudDetector().detect_fraud(
        {
            "amount": 31,
            "merchant_category": "grocery",
            "location_country": "US",
            "device_fingerprint": "known",
        },
        _history(),
    )
    assert alert.risk_level == RiskLevel.LOW
    assert alert.action == FraudAction.ALLOW
    assert alert.recommended_actions == ["allow_transaction"]


def test_detector_uses_model_and_explains(trained_ensemble):
    detector = RealTimeFraudDetector(trained_ensemble)
    alert = detector.detect_fraud(
        {
            "amount": 4000,
            "device_fingerprint": "stolen",
            "location_country": "RU",
            "merchant_category": "cryptocurrency",
        },
        _history(),
    )
    assert alert.metadata["mode"] == "model"
    assert alert.explanation["model_scores"]
    assert alert.explanation["primary_risk_factors"]
    assert 0.5 <= alert.confidence <= 1.0
    assert alert.is_flagged


def test_detector_falls_back_when_model_fails(trained_ensemble, monkeypatch):
    detector = RealTimeFraudDetector(trained_ensemble)
    monkeypatch.setattr(
        trained_ensemble,
        "predict_with_details",
        lambda *_: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    alert = detector.detect_fraud({"amount": 20000})
    assert alert.metadata["mode"] == "rules_only"


def test_detector_rejects_invalid_transaction():
    with pytest.raises(FraudDetectionError):
        RealTimeFraudDetector().detect_fraud({"amount": "NaN-ish"})


def test_explainer_importance_fallback():
    features = FeatureEngineer().extract_transaction_features(
        {"amount": 500, "user_id": "u"}
    )
    result = FraudExplainer().explain_prediction(
        features, 0.75, {"amount": 0.5, "velocity_1h": 0.2}
    )
    assert {
        "risk_score",
        "primary_risk_factors",
        "contributing_factors",
        "summary",
    } <= set(result)
    assert result["primary_risk_factors"][0]["feature"] == "amount"


@pytest.fixture
def service(settings, fast_config):
    return FraudDetectionService({"model_config": fast_config}, settings=settings)


def test_service_defaults_to_rules_only(service):
    status = service.get_model_status()
    assert status["mode"] == "rules_only"
    assert service.health()["status"] == "degraded"
    assert asyncio.run(service.check_retrain_needed()) is True


def test_service_detect_records_history_and_alerts(service):
    for _ in range(3):
        service.detect({"amount": 20, "user_id": "u9", "merchant_category": "grocery"})
    assert service.history_store.count("u9") == 3
    assert len(service.get_recent_alerts(1)) == 3
    stats = service.get_fraud_statistics(1)
    assert stats["total_transactions"] == 3


def test_service_blocked_transactions_do_not_pollute_history(service):
    alert = service.detect(
        {
            "amount": 50000,
            "user_id": "u8",
            "location_country": "KP",
            "merchant_category": "cryptocurrency",
        }
    )
    assert alert.action == FraudAction.BLOCK
    assert service.history_store.count("u8") == 0


def test_service_async_wrappers(service):
    alert = asyncio.run(service.detect_fraud({"amount": 10, "user_id": "a"}))
    assert alert.user_id == "a"
    alerts = asyncio.run(
        service.batch_detect_fraud(
            [{"amount": 10, "user_id": "a"}, {"amount": 11, "user_id": "b"}]
        )
    )
    assert len(alerts) == 2


def test_service_training_persists_and_reloads(settings, fast_config, labeled_data):
    service = FraudDetectionService({"model_config": fast_config}, settings=settings)
    features, labels = labeled_data
    result = service.train_model_sync(features, labels)
    assert result["promoted"] is True
    assert result["metrics"]["roc_auc"] > 0.9
    assert result["registry_version"]
    reloaded = FraudDetectionService({"model_config": fast_config}, settings=settings)
    assert reloaded.load_latest_model() is True
    assert reloaded.get_model_status()["mode"] == "model"


def test_service_feedback_updates_metrics_and_retrains(
    settings, fast_config, labeled_data
):
    service = FraudDetectionService({"model_config": fast_config}, settings=settings)
    features, labels = labeled_data
    service.train_model_sync(features, labels)
    alert = service.detect(
        {
            "amount": 30000,
            "user_id": "z",
            "transaction_id": "t-1",
            "location_country": "IR",
        }
    )
    assert service.record_feedback("t-1", True) is True
    assert service.record_feedback("missing", True) is False
    metrics = service.get_model_status()["performance_metrics"]
    assert metrics["true_positives"] + metrics["false_negatives"] == 1
    assert service.record_feedback("t-1", False) is True
    metrics = service.get_model_status()["performance_metrics"]
    assert metrics["true_positives"] == 0
    assert alert.transaction_id == "t-1"
    result = service.retrain_from_feedback(force=True)
    assert result["training_source"] == "feedback"


def test_champion_challenger_rejects_worse_model(settings, fast_config, labeled_data):
    service = FraudDetectionService({"model_config": fast_config}, settings=settings)
    features, labels = labeled_data
    service.train_model_sync(features, labels)
    incumbent = service.model_version()
    shuffled = labels.sample(frac=1.0, random_state=1).reset_index(drop=True)
    result = service.train_model_sync(features, shuffled, force=False)
    assert result["promoted"] is False
    assert service.model_version() == incumbent


def test_service_anomaly_and_velocity_helpers(service):
    anomaly = service.detect_anomalies(
        {
            "amount": 5000,
            "merchant_category": "cash_advance",
            "location": "Unknown Location",
            "time_of_day": 3,
        }
    )
    assert anomaly["is_anomaly"] is True and anomaly["anomaly_score"] > 0.7
    normal = service.analyze_transaction(
        {
            "amount": 100,
            "merchant_category": "grocery",
            "location": "New York, NY",
            "time_of_day": 14,
        }
    )
    assert normal["risk_level"] == "low" and normal["approved"] is True
    velocity = service.check_velocity(
        "u",
        [{"amount": 100 + i, "timestamp": "2024-01-15T10:00:00Z"} for i in range(4)],
    )
    assert velocity["transaction_count"] == 4 and velocity["velocity_exceeded"] is False


def test_service_drift_detection(settings, fast_config, labeled_data):
    service = FraudDetectionService({"model_config": fast_config}, settings=settings)
    features, labels = labeled_data
    service.train_model_sync(features, labels)
    for index in range(150):
        service.detect(
            {
                "amount": 9000 + index,
                "user_id": f"d{index}",
                "merchant_category": "cryptocurrency",
            }
        )
    report = service.drift_report()
    assert report["drifted"] is True
    assert "feature_drift_detected" in service.retrain_reasons()


def test_service_picks_up_model_promoted_by_another_worker(
    settings, fast_config, labeled_data
):
    trainer = FraudDetectionService({"model_config": fast_config}, settings=settings)
    follower = FraudDetectionService({"model_config": fast_config}, settings=settings)
    assert follower.model_ready is False
    features, labels = labeled_data
    trainer.train_model_sync(features, labels)
    assert follower.refresh_model_if_stale(min_interval_seconds=0.0) is True
    assert follower.model_ready is True
    assert follower.refresh_model_if_stale(min_interval_seconds=0.0) is False
