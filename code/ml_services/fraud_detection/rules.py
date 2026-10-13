from dataclasses import dataclass
from typing import List, Tuple

from ..core.enums import FraudType
from ..features.types import TransactionFeatures
from .types import RuleHit


@dataclass(frozen=True)
class RuleConfig:
    amount_elevated: float = 3000.0
    amount_high: float = 5000.0
    amount_very_high: float = 10000.0
    structuring_floor: float = 9000.0
    structuring_ceiling: float = 10000.0
    velocity_1h_limit: int = 8
    velocity_24h_limit: int = 30
    zscore_limit: float = 4.0
    rapid_country_change_minutes: float = 120.0
    new_user_high_value: float = 2000.0
    unusual_time_amount: float = 1000.0


def combine_scores(scores: List[float]) -> float:
    remaining = 1.0
    for score in scores:
        remaining *= 1.0 - min(max(score, 0.0), 1.0)
    return 1.0 - remaining


class RuleEngine:
    def __init__(self, config: RuleConfig = RuleConfig()) -> None:
        self.config = config

    def evaluate(self, f: TransactionFeatures) -> Tuple[float, List[RuleHit]]:
        c = self.config
        hits: List[RuleHit] = []
        amount = f.amount
        if amount >= c.amount_very_high:
            hits.append(
                RuleHit(
                    "very_high_amount",
                    0.6,
                    FraudType.PAYMENT_FRAUD,
                    "Transaction amount is very high",
                    {"amount": amount},
                )
            )
        elif amount >= c.amount_high:
            hits.append(
                RuleHit(
                    "high_amount",
                    0.4,
                    FraudType.PAYMENT_FRAUD,
                    "Transaction amount is high",
                    {"amount": amount},
                )
            )
        elif amount >= c.amount_elevated:
            hits.append(
                RuleHit(
                    "elevated_amount",
                    0.25,
                    FraudType.PAYMENT_FRAUD,
                    "Transaction amount is elevated",
                    {"amount": amount},
                )
            )
        if (f.velocity_1h or 0) >= c.velocity_1h_limit:
            hits.append(
                RuleHit(
                    "velocity_burst",
                    0.7,
                    FraudType.CARD_TESTING,
                    "Burst of transactions within one hour",
                    {"velocity_1h": f.velocity_1h},
                )
            )
        if (f.velocity_24h or 0) >= c.velocity_24h_limit:
            hits.append(
                RuleHit(
                    "daily_velocity",
                    0.45,
                    FraudType.PAYMENT_FRAUD,
                    "Unusually many transactions in 24 hours",
                    {"velocity_24h": f.velocity_24h},
                )
            )
        zscore = f.amount_zscore or 0.0
        if zscore >= c.zscore_limit and amount >= 100:
            hits.append(
                RuleHit(
                    "amount_outlier",
                    min(0.8, 0.3 + 0.05 * zscore),
                    FraudType.ACCOUNT_TAKEOVER,
                    "Amount deviates sharply from the user's history",
                    {"amount_zscore": round(zscore, 2)},
                )
            )
        if f.new_device and f.new_location:
            hits.append(
                RuleHit(
                    "new_device_and_location",
                    0.6,
                    FraudType.ACCOUNT_TAKEOVER,
                    "New device used from a new country",
                )
            )
        elif f.new_device and (f.amount_to_avg_ratio or 0) >= 3:
            hits.append(
                RuleHit(
                    "new_device_large_amount",
                    0.4,
                    FraudType.ACCOUNT_TAKEOVER,
                    "New device combined with an above average amount",
                )
            )
        elif f.new_device:
            hits.append(
                RuleHit(
                    "new_device",
                    0.2,
                    FraudType.ACCOUNT_TAKEOVER,
                    "Transaction from a device not seen before",
                )
            )
        if f.high_risk_country:
            hits.append(
                RuleHit(
                    "high_risk_country",
                    0.7,
                    FraudType.SANCTIONS_EXPOSURE,
                    "Transaction involves a high risk jurisdiction",
                    {"country": f.location_country},
                )
            )
        near_threshold = c.structuring_floor <= amount < c.structuring_ceiling
        round_cross_border = (
            amount >= c.amount_high and bool(f.is_round_amount) and bool(f.cross_border)
        )
        if near_threshold or round_cross_border:
            hits.append(
                RuleHit(
                    "structuring_pattern",
                    0.45,
                    FraudType.MONEY_LAUNDERING,
                    "Amount pattern is consistent with structuring",
                    {"amount": amount},
                )
            )
        if f.high_risk_merchant:
            hits.append(
                RuleHit(
                    "high_risk_merchant",
                    0.3,
                    FraudType.MERCHANT_FRAUD,
                    "Merchant category carries elevated risk",
                    {"merchant_category": f.merchant_category},
                )
            )
        if f.unknown_location:
            hits.append(
                RuleHit(
                    "unknown_location",
                    0.35,
                    FraudType.ACCOUNT_TAKEOVER,
                    "Transaction location could not be established",
                )
            )
        if f.unusual_time and amount >= c.unusual_time_amount:
            hits.append(
                RuleHit(
                    "unusual_time_large_amount",
                    0.2,
                    FraudType.PAYMENT_FRAUD,
                    "Large amount at an unusual hour",
                    {"hour": f.hour_of_day},
                )
            )
        if (
            f.last_country
            and f.location_country
            and f.last_country != f.location_country
            and (f.minutes_since_last_tx or 1e9) < c.rapid_country_change_minutes
        ):
            hits.append(
                RuleHit(
                    "rapid_country_change",
                    0.6,
                    FraudType.ACCOUNT_TAKEOVER,
                    "Country changed implausibly fast",
                    {"from": f.last_country, "to": f.location_country},
                )
            )
        if f.is_new_user and amount >= c.new_user_high_value:
            hits.append(
                RuleHit(
                    "new_user_high_value",
                    0.35,
                    FraudType.APPLICATION_FRAUD,
                    "High value transaction without prior history",
                )
            )
        return combine_scores([hit.score for hit in hits]), hits
