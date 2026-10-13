from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from ..core.logging import get_logger
from .categorizer import AITransactionCategorizer, parse_timestamp
from .types import SpendingAnalysis, SpendingPattern
from .types import TransactionCategory as C

logger = get_logger(__name__)

INFLOW_TYPES = {"credit", "deposit", "income", "refund", "interest"}
NON_SPEND = {C.INCOME, C.REFUNDS, C.TRANSFERS, C.INVESTMENTS}
RECURRING_PERIODS = ((7, 2), (14, 3), (30, 5), (91, 8), (365, 12))


def _is_inflow(tx: Dict[str, Any]) -> bool:
    return (
        str(tx.get("type") or tx.get("transaction_type") or "").lower() in INFLOW_TYPES
    )


def detect_recurring(
    transactions: List[Dict[str, Any]], min_occurrences: int = 3
) -> List[Dict[str, Any]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for tx in transactions:
        label = (
            str(
                tx.get("merchant_name")
                or tx.get("merchant")
                or tx.get("description")
                or ""
            )
            .strip()
            .lower()
        )
        stamp = parse_timestamp(tx.get("timestamp") or tx.get("created_at"))
        if not label or stamp is None or _is_inflow(tx):
            continue
        groups[label].append(
            {"timestamp": stamp, "amount": abs(float(tx.get("amount") or 0.0))}
        )
    found: List[Dict[str, Any]] = []
    for label, items in groups.items():
        if len(items) < min_occurrences:
            continue
        items.sort(key=lambda item: item["timestamp"])
        gaps = np.array(
            [
                (b["timestamp"] - a["timestamp"]).total_seconds() / 86400.0
                for a, b in zip(items, items[1:])
            ]
        )
        amounts = np.array([item["amount"] for item in items])
        median_gap = float(np.median(gaps))
        mean_amount = float(amounts.mean())
        if mean_amount <= 0 or float(amounts.std()) / mean_amount > 0.15:
            continue
        for period, tolerance in RECURRING_PERIODS:
            if (
                abs(median_gap - period) <= tolerance
                and float(np.mean(np.abs(gaps - period) <= tolerance * 1.5)) >= 0.6
            ):
                last = items[-1]["timestamp"]
                found.append(
                    {
                        "merchant": label,
                        "period_days": period,
                        "average_amount": round(mean_amount, 2),
                        "occurrences": len(items),
                        "next_expected": (last + timedelta(days=period)).isoformat(),
                    }
                )
                break
    found.sort(key=lambda item: -item["average_amount"])
    return found


def forecast_spending(
    daily_totals: Dict[str, float], horizon_days: int = 30
) -> Dict[str, Any]:
    if len(daily_totals) < 14:
        return {
            "horizon_days": horizon_days,
            "projected_spend": None,
            "method": "insufficient_data",
        }
    ordered = [daily_totals[key] for key in sorted(daily_totals)]
    weekly = np.array(
        [sum(ordered[i : i + 7]) for i in range(0, len(ordered) - 6, 7)], dtype=float
    )
    if len(weekly) < 2:
        return {
            "horizon_days": horizon_days,
            "projected_spend": None,
            "method": "insufficient_data",
        }
    x = np.arange(len(weekly))
    slope, intercept = np.polyfit(x, weekly, 1)
    weeks_ahead = horizon_days / 7.0
    future = np.array(
        [
            max(slope * (len(weekly) + i) + intercept, 0.0)
            for i in range(int(np.ceil(weeks_ahead)))
        ]
    )
    projected = float(future.sum() * (weeks_ahead / max(len(future), 1)))
    residual = weekly - (slope * x + intercept)
    margin = float(1.28 * residual.std() * np.sqrt(max(weeks_ahead, 1.0)))
    return {
        "horizon_days": horizon_days,
        "projected_spend": round(projected, 2),
        "lower_bound": round(max(projected - margin, 0.0), 2),
        "upper_bound": round(projected + margin, 2),
        "weekly_slope": round(float(slope), 2),
        "method": "linear_trend",
    }


class SpendingAnalyzer:
    def __init__(self, categorizer: Optional[AITransactionCategorizer] = None) -> None:
        self.categorizer = categorizer or AITransactionCategorizer()

    def analyze_spending_patterns(
        self,
        user_id: str,
        transactions: List[Dict[str, Any]],
        period_days: int = 90,
        income_hint: Optional[float] = None,
    ) -> SpendingAnalysis:
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
        scoped: List[Dict[str, Any]] = []
        for tx in transactions:
            stamp = parse_timestamp(tx.get("timestamp") or tx.get("created_at"))
            if stamp is None or stamp < cutoff:
                continue
            scoped.append({**tx, "_ts": stamp})
        totals: Dict[str, float] = defaultdict(float)
        daily: Dict[str, float] = defaultdict(float)
        income = 0.0
        spent = 0.0
        for tx in scoped:
            amount = abs(float(tx.get("amount") or 0.0))
            insight = self.categorizer.categorize_transaction(tx, user_id)
            if _is_inflow(tx) or insight.category == C.INCOME:
                income += amount
                continue
            if insight.category in NON_SPEND and insight.category != C.TRANSFERS:
                continue
            spent += amount
            totals[insight.category.value] += amount
            daily[tx["_ts"].date().isoformat()] += amount
        shares = (
            {name: value / spent for name, value in totals.items()} if spent else {}
        )
        trend = self._trend(daily)
        pattern = self._pattern(daily, trend)
        recurring = detect_recurring(scoped)
        income_basis = income if income else (income_hint or 0.0)
        analysis = SpendingAnalysis(
            user_id=user_id,
            period_days=period_days,
            total_spent=spent,
            total_income=income,
            net_cash_flow=income - spent,
            category_totals=dict(sorted(totals.items(), key=lambda item: -item[1])),
            category_shares=dict(sorted(shares.items(), key=lambda item: -item[1])),
            monthly_trend=trend,
            pattern=pattern,
            recurring=recurring,
            budget_recommendations=self._budget(totals, income_basis, period_days),
            insights=[],
            alerts=[],
            forecast=forecast_spending(daily, 30),
            transaction_count=len(scoped),
        )
        analysis.insights = self._insights(analysis)
        analysis.alerts = self._alerts(analysis)
        return analysis

    @staticmethod
    def _trend(daily: Dict[str, float]) -> float:
        if len(daily) < 14:
            return 0.0
        ordered = [daily[key] for key in sorted(daily)]
        half = len(ordered) // 2
        first, second = sum(ordered[:half]), sum(ordered[half:])
        if first <= 0:
            return 0.0
        return float(np.clip((second - first) / first, -1.0, 3.0))

    @staticmethod
    def _pattern(daily: Dict[str, float], trend: float) -> SpendingPattern:
        if len(daily) < 7:
            return SpendingPattern.REGULAR
        values = np.array(list(daily.values()), dtype=float)
        mean = float(values.mean()) or 1.0
        variation = float(values.std() / mean)
        if trend > 0.2:
            return SpendingPattern.INCREASING
        if trend < -0.2:
            return SpendingPattern.DECREASING
        if variation > 1.5:
            return SpendingPattern.VOLATILE
        if variation < 0.6:
            return SpendingPattern.STABLE
        return SpendingPattern.REGULAR

    @staticmethod
    def _budget(
        totals: Dict[str, float], income: float, period_days: int
    ) -> Dict[str, float]:
        months = max(period_days / 30.0, 1e-6)
        monthly_income = income / months if income else 0.0
        targets = {
            C.RESTAURANTS.value: 0.10,
            C.ENTERTAINMENT.value: 0.07,
            C.RETAIL_SHOPPING.value: 0.08,
            C.ONLINE_SHOPPING.value: 0.06,
            C.TRAVEL.value: 0.06,
        }
        recommendations: Dict[str, float] = {}
        for name, share in targets.items():
            current = totals.get(name, 0.0) / months
            if monthly_income:
                recommendations[name] = (
                    min(current, monthly_income * share)
                    if current > monthly_income * share
                    else current
                )
            elif current:
                recommendations[name] = current * 0.9
        for name in (
            C.GROCERIES.value,
            C.UTILITIES.value,
            C.TRANSPORTATION.value,
            C.HEALTHCARE.value,
        ):
            if name in totals:
                recommendations[name] = totals[name] / months
        return recommendations

    @staticmethod
    def _insights(analysis: SpendingAnalysis) -> List[str]:
        notes: List[str] = []
        if analysis.category_shares:
            top, share = next(iter(analysis.category_shares.items()))
            notes.append(
                f"Largest category is {top.replace('_', ' ')} at {share:.0%} of spending"
            )
        if analysis.total_income > 0:
            rate = analysis.net_cash_flow / analysis.total_income
            notes.append(f"Savings rate over the period is {rate:.0%}")
        if analysis.recurring:
            monthly = sum(
                item["average_amount"] * 30.0 / item["period_days"]
                for item in analysis.recurring
            )
            noun = "payment costs" if len(analysis.recurring) == 1 else "payments cost"
            notes.append(
                f"{len(analysis.recurring)} recurring {noun} about {monthly:.2f} per month"
            )
        if analysis.pattern in (SpendingPattern.INCREASING, SpendingPattern.DECREASING):
            notes.append(f"Spending is {analysis.pattern.value}")
        return notes

    @staticmethod
    def _alerts(analysis: SpendingAnalysis) -> List[str]:
        alerts: List[str] = []
        if analysis.total_income > 0 and analysis.net_cash_flow < 0:
            alerts.append("Spending exceeds income for the period")
        if analysis.monthly_trend > 0.5:
            alerts.append(
                "Spending increased sharply compared with the earlier half of the period"
            )
        if analysis.pattern == SpendingPattern.VOLATILE:
            alerts.append("Spending is highly volatile")
        return alerts

    def update_user_profile(
        self, user_id: str, transaction: Dict[str, Any], category: str
    ) -> bool:
        return self.categorizer.update_user_profile(user_id, transaction, category)
