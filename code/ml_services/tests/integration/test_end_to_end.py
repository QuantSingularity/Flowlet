from ml_services.data import generate_transaction_stream
from ml_services.fraud_detection import FraudDetectionService
from ml_services.serving import MLServiceContainer
from ml_services.training import build_training_frame, train_ensemble
from ml_services.training.cli import main as cli_main


def test_stream_training_pipeline_detects_fraud(fast_config, settings):
    stream = generate_transaction_stream(60, 40, fraud_rate=0.06, seed=21)
    features, labels = build_training_frame(stream, settings=settings)
    assert len(features) == len(stream) and labels.sum() > 10
    result = train_ensemble(
        features, labels, model_config=fast_config, settings=settings
    )
    assert result.metrics["roc_auc"] > 0.85
    assert result.holdout_samples > 0


def test_service_scoring_over_labeled_stream(settings, fast_config):
    train_stream = generate_transaction_stream(60, 40, fraud_rate=0.06, seed=31)
    service = FraudDetectionService({"model_config": fast_config}, settings=settings)
    service.train_from_transactions(train_stream)
    test_stream = generate_transaction_stream(15, 40, fraud_rate=0.08, seed=77)
    alerts = service.batch_detect(test_stream)
    flagged_fraud = sum(
        1 for a, t in zip(alerts, test_stream) if a.is_flagged and t["is_fraud"]
    )
    total_fraud = sum(t["is_fraud"] for t in test_stream)
    false_alarms = sum(
        1 for a, t in zip(alerts, test_stream) if a.is_flagged and not t["is_fraud"]
    )
    assert flagged_fraud / max(total_fraud, 1) >= 0.5
    assert false_alarms / len(test_stream) < 0.1


def test_container_wires_all_components(settings):
    container = MLServiceContainer(settings)
    assert container.spending.categorizer is container.categorizer
    health = container.health()
    assert health["components"]["support_chatbot"] == "ready"


def test_cli_trains_and_lists(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ML_MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("ML_ARTIFACT_SIGNING_KEY", "cli-key")
    monkeypatch.setenv("ML_PERSIST_MODELS", "true")
    from ml_services.config import reload_settings

    reload_settings()
    try:
        monkeypatch.setattr(
            "ml_services.training.pipeline.default_model_config",
            lambda: {
                "voting_strategy": "weighted",
                "models": {
                    "isolation_forest": {"n_estimators": 20},
                    "random_forest": {"n_estimators": 20},
                },
            },
        )
        assert cli_main(["train-synthetic", "--samples", "1200"]) == 0
        capsys.readouterr()
        assert cli_main(["list"]) == 0
        assert capsys.readouterr().out.strip().startswith("*")
    finally:
        monkeypatch.undo()
        reload_settings()
