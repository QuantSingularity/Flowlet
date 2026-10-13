import math
from datetime import timedelta
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from ..config import MLSettings, get_settings
from ..core.exceptions import FeatureExtractionError, InvalidTransactionError
from ..core.logging import get_logger
from ..data.validation import normalize_transaction
from .history import normalize_history
from .schema import FEATURE_COLUMNS, HIGH_RISK_CATEGORIES
from .types import TransactionFeatures

logger = get_logger(__name__)

NO_PRIOR_TRANSACTION_MINUTES = 10080.0
MIN_HISTORY_FOR_PERSONALIZATION = 10


class FeatureEngineer:
    def __init__(self, settings: Optional[MLSettings] = None) -> None:
        self.settings = settings or get_settings()

    def extract_transaction_features(
        self, transaction_data: Dict[str, Any], user_history: Any = None
    ) -> TransactionFeatures:
        try:
            tx = (
                transaction_data
                if transaction_data.get("_normalized")
                else normalize_transaction(transaction_data)
            )
        except InvalidTransactionError as exc:
            raise FeatureExtractionError(f"Feature extraction error: {exc}") from exc
        try:
            return self._build(tx, normalize_history(user_history))
        except FeatureExtractionError:
            raise
        except Exception as exc:
            logger.error("Feature extraction failed: %s", exc)
            raise FeatureExtractionError(f"Feature extraction error: {exc}") from exc

    def _build(self, tx: Dict[str, Any], history: pd.DataFrame) -> TransactionFeatures:
        timestamp = tx["timestamp"]
        amount = tx["amount"]
        category = tx.get("merchant_category")
        country = tx.get("location_country")
        device = tx.get("device_fingerprint")
        hour = timestamp.hour
        past = (
            history[history["timestamp"] <= timestamp] if not history.empty else history
        )
        has_history = not past.empty
        features = TransactionFeatures(
            transaction_id=tx["transaction_id"],
            user_id=tx["user_id"],
            amount=amount,
            currency=tx["currency"],
            timestamp=timestamp,
            merchant_category=category,
            location_country=country,
            location_city=tx.get("location_city"),
            device_fingerprint=device,
            ip_address=tx.get("ip_address"),
            payment_method=tx.get("payment_method"),
            channel=tx.get("channel"),
        )
        features.hour_of_day = hour
        features.day_of_week = timestamp.weekday()
        features.is_weekend = timestamp.weekday() >= 5
        features.amount_log = float(math.log1p(amount))
        features.is_round_amount = bool(amount >= 100 and float(amount) % 100 == 0)
        features.high_risk_merchant = bool(
            category and category in HIGH_RISK_CATEGORIES
        )
        features.high_risk_country = bool(
            country and country in self.settings.high_risk_countries
        )
        raw_location = (tx.get("location_raw") or "").lower()
        features.unknown_location = bool("unknown" in raw_location)
        features.unusual_time = bool(hour < 6 or hour >= 23)
        features.is_new_user = not has_history
        features.velocity_1h = 0
        features.velocity_24h = 0
        features.velocity_7d = 0
        features.user_age_days = 0
        features.avg_transaction_amount = 0.0
        features.transaction_count_30d = 0
        features.unique_merchants_30d = 0
        features.amount_zscore = 0.0
        features.amount_to_avg_ratio = 1.0
        features.new_device = False
        features.new_location = False
        features.cross_border = False
        features.minutes_since_last_tx = NO_PRIOR_TRANSACTION_MINUTES
        features.amount_24h_total = amount
        features.distinct_devices_7d = 1 if device else 0
        if has_history:
            self._apply_history(features, past, timestamp)
        return features

    def _apply_history(
        self, features: TransactionFeatures, past: pd.DataFrame, timestamp: Any
    ) -> None:
        stamps = past["timestamp"]
        amounts = past["amount"].astype(float)
        features.velocity_1h = int((stamps > timestamp - timedelta(hours=1)).sum())
        day_mask = stamps > timestamp - timedelta(hours=24)
        features.velocity_24h = int(day_mask.sum())
        week_mask = stamps > timestamp - timedelta(days=7)
        features.velocity_7d = int(week_mask.sum())
        features.user_age_days = max(0, int((timestamp - stamps.min()).days))
        month_mask = stamps > timestamp - timedelta(days=30)
        month = past[month_mask]
        if not month.empty:
            avg = float(month["amount"].astype(float).mean())
            features.avg_transaction_amount = avg
            features.transaction_count_30d = int(len(month))
            features.unique_merchants_30d = int(month["merchant_category"].nunique())
            if avg > 0:
                features.amount_to_avg_ratio = float(min(features.amount / avg, 100.0))
        if len(amounts) >= 3:
            mean = float(amounts.mean())
            std = float(amounts.std(ddof=1)) if len(amounts) > 1 else 0.0
            if not std or not math.isfinite(std):
                std = max(mean * 0.5, 1.0)
            features.amount_zscore = float(
                np.clip((features.amount - mean) / std, -50, 50)
            )
        last = stamps.max()
        features.minutes_since_last_tx = float(
            min((timestamp - last).total_seconds() / 60.0, NO_PRIOR_TRANSACTION_MINUTES)
        )
        features.amount_24h_total = float(amounts[day_mask].sum() + features.amount)
        devices = past.loc[week_mask, "device_fingerprint"].dropna()
        device_set = set(devices.astype(str))
        if features.device_fingerprint:
            device_set.add(features.device_fingerprint)
        features.distinct_devices_7d = int(len(device_set))
        known_devices = set(past["device_fingerprint"].dropna().astype(str))
        if features.device_fingerprint and known_devices:
            features.new_device = features.device_fingerprint not in known_devices
        countries = past["location_country"].dropna().astype(str)
        known_countries = set(countries)
        if features.location_country and known_countries:
            features.new_location = features.location_country not in known_countries
            top = countries.mode()
            if not top.empty:
                features.cross_border = features.location_country != top.iloc[0]
        if not countries.empty:
            last_row = past.sort_values("timestamp").iloc[-1]
            last_country = last_row["location_country"]
            features.last_country = str(last_country) if last_country else None
        if len(past) >= MIN_HISTORY_FOR_PERSONALIZATION:
            hours = stamps.dt.hour
            near = hours.apply(
                lambda h: min(
                    (h - features.hour_of_day) % 24, (features.hour_of_day - h) % 24
                )
                <= 1
            )
            features.unusual_time = bool(near.mean() < 0.05)

    def features_to_row(self, features: TransactionFeatures) -> Dict[str, float]:
        row: Dict[str, float] = {}
        for column in FEATURE_COLUMNS:
            value = getattr(features, column, 0)
            if value is None:
                value = 0
            row[column] = float(value)
        return row

    def features_to_dataframe(self, features: TransactionFeatures) -> pd.DataFrame:
        return pd.DataFrame([self.features_to_row(features)], columns=FEATURE_COLUMNS)

    def batch_to_dataframe(self, items: Iterable[TransactionFeatures]) -> pd.DataFrame:
        rows: List[Dict[str, float]] = [self.features_to_row(item) for item in items]
        return pd.DataFrame(rows, columns=FEATURE_COLUMNS)
