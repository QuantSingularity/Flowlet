import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..features.schema import FEATURE_COLUMNS

_CATEGORIES = [
    "grocery",
    "restaurant",
    "gas",
    "retail",
    "utilities",
    "travel",
    "entertainment",
    "healthcare",
]
_COUNTRIES = ["US", "GB", "DE", "FR", "CA", "AU", "AE", "PK"]
_RISK_COUNTRIES = ["KP", "IR", "MM"]


def _legitimate(rng: np.random.Generator, n: int) -> Dict[str, np.ndarray]:
    avg = rng.lognormal(3.6, 0.6, n)
    ratio = rng.lognormal(0.0, 0.5, n)
    amount = avg * ratio
    rounded = rng.random(n) < 0.03
    amount = np.where(
        rounded, np.maximum(100.0, np.ceil(amount / 100.0) * 100.0), amount
    )
    hour = np.clip(rng.normal(14, 4.5, n), 0, 23).astype(int)
    unusual = rng.random(n) < 0.04
    hour = np.where(unusual, rng.choice([0, 1, 2, 3, 4, 5, 23], n), hour)
    v1 = rng.poisson(0.3, n)
    v24 = v1 + rng.poisson(2.0, n)
    v7 = v24 + rng.poisson(8.0, n)
    age = rng.exponential(400.0, n).astype(int) + 1
    new_user = rng.random(n) < 0.03
    new_device = rng.random(n) < 0.03
    new_location = rng.random(n) < 0.02
    return {
        "amount": amount,
        "avg": avg,
        "hour": hour,
        "v1": v1,
        "v24": v24,
        "v7": v7,
        "age": age,
        "new_user": new_user,
        "new_device": new_device,
        "new_location": new_location,
        "high_risk_merchant": rng.random(n) < 0.02,
        "high_risk_country": rng.random(n) < 0.002,
        "cross_border": rng.random(n) < 0.04,
        "minutes": np.minimum(rng.exponential(600.0, n), 10080.0),
        "devices": 1 + rng.poisson(0.2, n),
        "count30": rng.poisson(15, n),
        "merchants": rng.poisson(4, n) + 1,
        "zscore": (ratio - 1.0) / 0.6,
        "ratio": ratio,
    }


def _fraudulent(rng: np.random.Generator, n: int) -> Dict[str, np.ndarray]:
    base = _legitimate(rng, n)
    kind = rng.choice(5, size=n, p=[0.30, 0.22, 0.22, 0.14, 0.12])
    takeover = kind == 0
    testing = kind == 1
    high_value = kind == 2
    structuring = kind == 3
    subtle = kind == 4
    ratio = base["ratio"].copy()
    amount = base["amount"].copy()
    avg = base["avg"]
    ratio = np.where(takeover, rng.lognormal(1.4, 0.5, n), ratio)
    amount = np.where(takeover, avg * ratio, amount)
    base["new_device"] = np.where(takeover, rng.random(n) < 0.9, base["new_device"])
    base["new_location"] = np.where(takeover, rng.random(n) < 0.7, base["new_location"])
    base["cross_border"] = np.where(takeover, rng.random(n) < 0.6, base["cross_border"])
    base["v1"] = np.where(takeover, rng.poisson(2.5, n), base["v1"])
    base["devices"] = np.where(takeover, 2 + rng.poisson(0.6, n), base["devices"])
    unusual_hours = rng.choice([0, 1, 2, 3, 4, 5, 23], n)
    base["hour"] = np.where(
        takeover & (rng.random(n) < 0.5), unusual_hours, base["hour"]
    )
    amount = np.where(testing, rng.uniform(1.0, 10.0, n), amount)
    ratio = np.where(testing, amount / np.maximum(avg, 1.0), ratio)
    base["v1"] = np.where(testing, rng.poisson(8, n) + 3, base["v1"])
    base["v24"] = np.where(testing, base["v1"] + rng.poisson(10, n), base["v24"])
    base["minutes"] = np.where(testing, rng.uniform(0.0, 2.0, n), base["minutes"])
    base["new_device"] = np.where(testing, rng.random(n) < 0.4, base["new_device"])
    base["high_risk_merchant"] = np.where(
        testing, rng.random(n) < 0.3, base["high_risk_merchant"]
    )
    amount = np.where(high_value, rng.lognormal(8.0, 0.8, n), amount)
    ratio = np.where(high_value, amount / np.maximum(avg, 1.0), ratio)
    base["unusual_hour"] = high_value & (rng.random(n) < 0.4)
    base["hour"] = np.where(base["unusual_hour"], unusual_hours, base["hour"])
    base["high_risk_merchant"] = np.where(
        high_value, rng.random(n) < 0.35, base["high_risk_merchant"]
    )
    base["new_location"] = np.where(
        high_value, rng.random(n) < 0.3, base["new_location"]
    )
    structured = rng.choice([5000.0, 9000.0, 9500.0, 9900.0, 10000.0], n)
    amount = np.where(structuring, structured, amount)
    ratio = np.where(structuring, amount / np.maximum(avg, 1.0), ratio)
    base["cross_border"] = np.where(
        structuring, rng.random(n) < 0.8, base["cross_border"]
    )
    base["high_risk_country"] = np.where(
        structuring, rng.random(n) < 0.35, base["high_risk_country"]
    )
    base["v24"] = np.where(structuring, base["v24"] + rng.poisson(6, n), base["v24"])
    elevated = rng.integers(0, 3, n)
    amount = np.where(
        subtle & (elevated == 0), avg * rng.lognormal(0.9, 0.3, n), amount
    )
    base["new_device"] = np.where(
        subtle & (elevated == 1), rng.random(n) < 0.8, base["new_device"]
    )
    base["v1"] = np.where(subtle & (elevated == 2), rng.poisson(3, n), base["v1"])
    ratio = np.where(subtle & (elevated == 0), amount / np.maximum(avg, 1.0), ratio)
    base["amount"] = amount
    base["ratio"] = ratio
    base["zscore"] = (ratio - 1.0) / 0.6
    base["v24"] = np.maximum(base["v24"], base["v1"])
    base["v7"] = np.maximum(base["v7"], base["v24"])
    return base


def _assemble(raw: Dict[str, np.ndarray], rng: np.random.Generator) -> pd.DataFrame:
    n = len(raw["amount"])
    amount = np.maximum(raw["amount"], 0.01)
    new_user = raw["new_user"].astype(bool)
    hour = raw["hour"].astype(int)
    dow = rng.integers(0, 7, n)
    unusual = (hour < 6) | (hour >= 23)
    day_total = amount + raw["v24"] * raw["avg"] * rng.lognormal(0.0, 0.3, n)
    frame = pd.DataFrame(
        {
            "amount": amount,
            "hour_of_day": hour,
            "day_of_week": dow,
            "is_weekend": (dow >= 5).astype(int),
            "amount_zscore": np.clip(raw["zscore"], -50, 50),
            "velocity_1h": raw["v1"],
            "velocity_24h": raw["v24"],
            "velocity_7d": raw["v7"],
            "user_age_days": raw["age"],
            "avg_transaction_amount": raw["avg"],
            "transaction_count_30d": raw["count30"],
            "unique_merchants_30d": raw["merchants"],
            "new_device": raw["new_device"].astype(int),
            "new_location": raw["new_location"].astype(int),
            "unusual_time": unusual.astype(int),
            "high_risk_merchant": raw["high_risk_merchant"].astype(int),
            "amount_log": np.log1p(amount),
            "amount_to_avg_ratio": np.clip(
                amount / np.maximum(raw["avg"], 1e-6), 0, 100
            ),
            "is_round_amount": ((amount >= 100) & (np.mod(amount, 100.0) == 0)).astype(
                int
            ),
            "minutes_since_last_tx": raw["minutes"],
            "amount_24h_total": day_total,
            "distinct_devices_7d": raw["devices"],
            "high_risk_country": raw["high_risk_country"].astype(int),
            "cross_border": raw["cross_border"].astype(int),
            "is_new_user": new_user.astype(int),
        }
    )
    reset = frame["is_new_user"] == 1
    for column in (
        "user_age_days",
        "velocity_1h",
        "velocity_24h",
        "velocity_7d",
        "avg_transaction_amount",
        "transaction_count_30d",
        "unique_merchants_30d",
        "amount_zscore",
    ):
        frame.loc[reset, column] = 0
    frame.loc[reset, "amount_to_avg_ratio"] = 1.0
    frame.loc[reset, "minutes_since_last_tx"] = 10080.0
    return frame[FEATURE_COLUMNS].astype(float)


def generate_labeled_features(
    n_samples: int = 5000,
    fraud_rate: float = 0.06,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.Series]:
    if n_samples < 20:
        raise ValueError("n_samples must be at least 20")
    if not 0.0 < fraud_rate < 0.5:
        raise ValueError("fraud_rate must be between 0 and 0.5")
    rng = np.random.default_rng(seed)
    n_fraud = max(2, int(round(n_samples * fraud_rate)))
    n_legit = n_samples - n_fraud
    legit = _assemble(_legitimate(rng, n_legit), rng)
    fraud = _assemble(_fraudulent(rng, n_fraud), rng)
    features = pd.concat([legit, fraud], ignore_index=True)
    labels = pd.Series(
        np.concatenate([np.zeros(n_legit, dtype=int), np.ones(n_fraud, dtype=int)]),
        name="is_fraud",
    )
    order = rng.permutation(len(features))
    return (
        features.iloc[order].reset_index(drop=True),
        labels.iloc[order].reset_index(drop=True),
    )


def generate_transaction_stream(
    n_users: int = 20,
    transactions_per_user: int = 40,
    fraud_rate: float = 0.05,
    seed: int = 7,
    start: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed)
    start = start or (datetime.now(timezone.utc) - timedelta(days=60))
    stream: List[Dict[str, Any]] = []
    for user_index in range(n_users):
        user_id = f"synthetic-user-{user_index:04d}"
        home = str(rng.choice(_COUNTRIES))
        devices = [f"dev-{user_index}-{k}" for k in range(int(rng.integers(1, 3)))]
        avg = float(rng.lognormal(3.6, 0.5))
        cursor = start + timedelta(hours=float(rng.uniform(0, 24)))
        for _ in range(transactions_per_user):
            cursor += timedelta(hours=float(rng.exponential(30.0)))
            hour = int(np.clip(rng.normal(14, 4), 6, 22))
            moment = cursor.replace(hour=hour, minute=int(rng.integers(0, 60)))
            category = str(rng.choice(_CATEGORIES))
            amount = float(avg * rng.lognormal(0.0, 0.5))
            record: Dict[str, Any] = {
                "transaction_id": str(uuid.uuid4()),
                "user_id": user_id,
                "amount": round(amount, 2),
                "currency": "USD",
                "timestamp": moment.isoformat(),
                "merchant_category": category,
                "location_country": home,
                "device_fingerprint": str(rng.choice(devices)),
                "is_fraud": 0,
            }
            if rng.random() < fraud_rate:
                kind = int(rng.integers(0, 3))
                record["is_fraud"] = 1
                if kind == 0:
                    record["amount"] = round(avg * float(rng.uniform(6, 15)), 2)
                    record["device_fingerprint"] = f"stolen-{uuid.uuid4().hex[:8]}"
                    record["location_country"] = str(
                        rng.choice(_RISK_COUNTRIES + _COUNTRIES)
                    )
                    record["timestamp"] = moment.replace(
                        hour=int(rng.integers(0, 5))
                    ).isoformat()
                elif kind == 1:
                    record["amount"] = round(float(rng.uniform(1, 9)), 2)
                    record["merchant_category"] = "cryptocurrency"
                    record["device_fingerprint"] = f"bot-{uuid.uuid4().hex[:8]}"
                else:
                    record["amount"] = float(rng.choice([5000, 9000, 9500, 9900]))
                    record["location_country"] = str(rng.choice(_RISK_COUNTRIES))
                    record["merchant_category"] = "wire_transfer"
            if not math.isfinite(record["amount"]):
                continue
            stream.append(record)
    stream.sort(key=lambda item: item["timestamp"])
    return stream
