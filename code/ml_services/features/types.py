from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class TransactionFeatures:
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    timestamp: datetime
    merchant_category: Optional[str] = None
    location_country: Optional[str] = None
    location_city: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    payment_method: Optional[str] = None
    channel: Optional[str] = None
    hour_of_day: Optional[int] = None
    day_of_week: Optional[int] = None
    is_weekend: Optional[bool] = None
    amount_zscore: Optional[float] = None
    velocity_1h: Optional[int] = None
    velocity_24h: Optional[int] = None
    velocity_7d: Optional[int] = None
    user_age_days: Optional[int] = None
    avg_transaction_amount: Optional[float] = None
    transaction_count_30d: Optional[int] = None
    unique_merchants_30d: Optional[int] = None
    new_device: Optional[bool] = None
    new_location: Optional[bool] = None
    unusual_time: Optional[bool] = None
    high_risk_merchant: Optional[bool] = None
    amount_log: Optional[float] = None
    amount_to_avg_ratio: Optional[float] = None
    is_round_amount: Optional[bool] = None
    minutes_since_last_tx: Optional[float] = None
    amount_24h_total: Optional[float] = None
    distinct_devices_7d: Optional[int] = None
    high_risk_country: Optional[bool] = None
    cross_border: Optional[bool] = None
    is_new_user: Optional[bool] = None
    last_country: Optional[str] = None
    unknown_location: Optional[bool] = None
    extras: Dict[str, Any] = field(default_factory=dict)
