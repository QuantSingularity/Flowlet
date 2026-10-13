import statistics
import time

from ml_services.fraud_detection import FraudDetectionService


def test_scoring_latency_budget(settings, fast_config, labeled_data):
    service = FraudDetectionService({"model_config": fast_config}, settings=settings)
    features, labels = labeled_data
    service.train_model_sync(features, labels)
    payload = {"amount": 120.0, "user_id": "perf", "merchant_category": "grocery"}
    service.detect(payload)
    samples = []
    for _ in range(40):
        started = time.perf_counter()
        service.detect(payload)
        samples.append((time.perf_counter() - started) * 1000.0)
    assert statistics.median(samples) < 150.0


def test_rules_only_latency(settings):
    service = FraudDetectionService({}, settings=settings)
    started = time.perf_counter()
    for index in range(200):
        service.detect({"amount": 10 + index, "user_id": f"u{index % 10}"})
    per_call = (time.perf_counter() - started) / 200 * 1000.0
    assert per_call < 25.0
