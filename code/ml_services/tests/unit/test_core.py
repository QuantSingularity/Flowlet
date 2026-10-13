import pytest
from ml_services.core import (
    FraudAction,
    ModelIntegrityError,
    ModelNotFoundError,
    ModelRegistry,
    RiskLevel,
)


def test_risk_level_thresholds():
    assert RiskLevel.from_score(0.1) == RiskLevel.LOW
    assert RiskLevel.from_score(0.4) == RiskLevel.MEDIUM
    assert RiskLevel.from_score(0.7) == RiskLevel.HIGH
    assert RiskLevel.from_score(0.9) == RiskLevel.CRITICAL
    assert RiskLevel.CRITICAL.at_least(RiskLevel.HIGH)
    assert not RiskLevel.LOW.at_least(RiskLevel.MEDIUM)


def test_action_mapping():
    assert FraudAction.for_level(RiskLevel.LOW) == FraudAction.ALLOW
    assert FraudAction.for_level(RiskLevel.CRITICAL) == FraudAction.BLOCK


def test_registry_roundtrip_and_versions(tmp_path):
    registry = ModelRegistry(tmp_path, "key", keep_versions=2)
    first = registry.save("model", {"v": 1}, {"note": "a"})
    second = registry.save("model", {"v": 2})
    assert registry.current_version("model") == second
    artifact, manifest = registry.load("model")
    assert artifact == {"v": 2}
    assert manifest["version"] == second
    registry.promote("model", first)
    assert registry.load("model")[0] == {"v": 1}
    registry.save("model", {"v": 3})
    assert len(registry.list_versions("model")) == 2


def test_registry_detects_tampering(tmp_path):
    registry = ModelRegistry(tmp_path, "key")
    version = registry.save("model", {"v": 1})
    path = tmp_path / "model" / version / "model.joblib"
    path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(ModelIntegrityError):
        registry.load("model")


def test_registry_rejects_wrong_key(tmp_path):
    ModelRegistry(tmp_path, "key-a").save("model", {"v": 1})
    with pytest.raises(ModelIntegrityError):
        ModelRegistry(tmp_path, "key-b").load("model")


def test_registry_rejects_path_traversal(tmp_path):
    registry = ModelRegistry(tmp_path, "key")
    with pytest.raises(ValueError):
        registry.save("../escape", {"v": 1})


def test_registry_missing_model(tmp_path):
    with pytest.raises(ModelNotFoundError):
        ModelRegistry(tmp_path, "key").load("absent")
