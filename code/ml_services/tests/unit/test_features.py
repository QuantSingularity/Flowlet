from datetime import datetime, timedelta, timezone

import pytest
from ml_services.core import FeatureExtractionError, InvalidTransactionError
from ml_services.data import generate_labeled_features, normalize_transaction
from ml_services.features import (
    FEATURE_COLUMNS,
    FeatureEngineer,
    InMemoryHistoryStore,
    normalize_history,
)


def _history(count=30, country="US", device="d1"):
    now = datetime.now(timezone.utc)
    return [
        {
            "timestamp": (now - timedelta(hours=index + 1)).isoformat(),
            "amount": 20 + (index % 5),
            "location_country": country,
            "device_fingerprint": device,
            "merchant_category": "grocery",
        }
        for index in range(count)
    ]


def test_normalize_transaction_aliases_and_validation():
    tx = normalize_transaction(
        {"amount": "100.5", "location": "Karachi, PK", "time_of_day": 14}
    )
    assert tx["amount"] == 100.5
    assert tx["location_country"] == "PK"
    assert tx["timestamp"].hour == 14
    assert (
        normalize_transaction({"amount": 1, "location": "New York, NY"})[
            "location_country"
        ]
        is None
    )


@pytest.mark.parametrize("amount", ["abc", -5, float("inf"), None, True])
def test_normalize_rejects_bad_amounts(amount):
    with pytest.raises(InvalidTransactionError):
        normalize_transaction({"amount": amount})


def test_normalize_rejects_bad_currency_and_timestamp():
    with pytest.raises(InvalidTransactionError):
        normalize_transaction({"amount": 1, "currency": "DOLLARS"})
    with pytest.raises(InvalidTransactionError):
        normalize_transaction({"amount": 1, "timestamp": "yesterday"})


def test_features_reflect_history():
    engineer = FeatureEngineer()
    features = engineer.extract_transaction_features(
        {
            "amount": 900,
            "user_id": "u",
            "device_fingerprint": "new",
            "location_country": "RU",
        },
        _history(),
    )
    assert features.velocity_24h >= 20
    assert features.new_device is True
    assert features.new_location is True
    assert features.cross_border is True
    assert features.amount_zscore > 3
    assert features.is_new_user is False


def test_features_for_new_user_have_defaults():
    features = FeatureEngineer().extract_transaction_features({"amount": 10})
    assert features.is_new_user is True
    assert features.velocity_1h == 0
    row = FeatureEngineer().features_to_row(features)
    assert list(row) == FEATURE_COLUMNS


def test_future_history_is_ignored():
    future = [
        {
            "timestamp": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "amount": 10,
        }
    ]
    features = FeatureEngineer().extract_transaction_features({"amount": 10}, future)
    assert features.velocity_24h == 0
    assert features.is_new_user is True


def test_invalid_input_raises_feature_error():
    with pytest.raises(FeatureExtractionError):
        FeatureEngineer().extract_transaction_features({"amount": "bad"})


def test_normalize_history_handles_mixed_inputs():
    assert normalize_history(None).empty
    assert normalize_history([]).empty
    frame = normalize_history([{"timestamp": "2024-01-01T00:00:00", "amount": "5"}])
    assert len(frame) == 1
    assert str(frame["timestamp"].dt.tz) == "UTC"


def test_history_store_bounds_and_window():
    store = InMemoryHistoryStore(max_per_user=5, window_days=30)
    for index in range(10):
        store.append("u", {"timestamp": datetime.now(timezone.utc), "amount": index})
    assert store.count("u") == 5
    assert len(store.get("u")) == 5
    store.append(
        "old",
        {"timestamp": datetime.now(timezone.utc) - timedelta(days=90), "amount": 1},
    )
    assert store.get("old").empty
    store.clear()
    assert store.count("u") == 0


def test_synthetic_data_shape_and_balance():
    features, labels = generate_labeled_features(1000, 0.1, 5)
    assert list(features.columns) == FEATURE_COLUMNS
    assert features.isna().sum().sum() == 0
    assert abs(labels.mean() - 0.1) < 0.01
    again, _ = generate_labeled_features(1000, 0.1, 5)
    assert features.equals(again)
