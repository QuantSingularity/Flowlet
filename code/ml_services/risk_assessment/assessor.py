import hashlib
import math
import threading
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, Deque, Dict, List, Optional

import numpy as np
import pandas as pd

from ..core.logging import get_logger
from .types import RiskAssessment, RiskCategory, RiskFactor, RiskTier

logger = get_logger(__name__)

CATEGORY_WEIGHTS = {
    RiskCategory.CREDIT_RISK: 0.25,
    RiskCategory.FRAUD_RISK: 0.35,
    RiskCategory.LIQUIDITY_RISK: 0.2,
    RiskCategory.OPERATIONAL_RISK: 0.1,
    RiskCategory.COMPLIANCE_RISK: 0.1,
}

KYC_SCORES = {
    "verified": 0.05,
    "completed": 0.05,
    "approved": 0.05,
    "pending": 0.5,
    "in_progress": 0.5,
    "not_started": 0.7,
    "rejected": 0.95,
    "failed": 0.95,
    "expired": 0.7,
}

HISTORY_BOUND = 50


def _clip(value: float) -> float:
    return float(min(max(value, 0.0), 1.0))


def _logistic(value: float, midpoint: float, steepness: float) -> float:
    return 1.0 / (1.0 + math.exp(-steepness * (value - midpoint)))


class AIRiskAssessor:
    def __init__(self) -> None:
        self._history: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=HISTORY_BOUND)
        )
        self._lock = threading.Lock()

    def assess_user_risk(
        self,
        user_id: str,
        assessment_context: Optional[Dict[str, Any]] = None,
        user_data: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessment:
        data = dict(user_data or {})
        context = assessment_context or {}
        data.update({k: v for k, v in context.items() if k not in data})
        transactions = self._transactions(data)
        factors: List[RiskFactor] = []
        builders = (
            (RiskCategory.CREDIT_RISK, self._credit),
            (RiskCategory.FRAUD_RISK, self._fraud),
            (RiskCategory.LIQUIDITY_RISK, self._liquidity),
            (RiskCategory.OPERATIONAL_RISK, self._operational),
            (RiskCategory.COMPLIANCE_RISK, self._compliance),
        )
        category_scores: Dict[str, float] = {}
        for category, builder in builders:
            produced = builder(data, transactions)
            factors.extend(produced)
            category_scores[category.value] = self._category_score(produced)
        overall = self._overall(category_scores)
        completeness = self._completeness(data, transactions)
        confidence = self._confidence(completeness, transactions)
        level = RiskTier.from_score(overall)
        predictions = self._predictions(data, transactions, category_scores, overall)
        assessment = RiskAssessment(
            user_id=user_id,
            assessment_id=self._assessment_id(user_id),
            timestamp=datetime.now(timezone.utc),
            overall_risk_score=overall,
            overall_risk_level=level,
            risk_factors=factors,
            category_scores=category_scores,
            predictions=predictions,
            recommendations=self._recommendations(factors, level),
            monitoring_alerts=self._alerts(factors, predictions),
            confidence_score=confidence,
            data_completeness=completeness,
        )
        with self._lock:
            self._history[user_id].append(
                {
                    "assessment_id": assessment.assessment_id,
                    "timestamp": assessment.timestamp,
                    "score": overall,
                    "level": level.value,
                }
            )
        return assessment

    @staticmethod
    def _transactions(data: Dict[str, Any]) -> pd.DataFrame:
        columns = [
            "timestamp",
            "amount",
            "type",
            "status",
            "merchant_category",
            "device_fingerprint",
            "location_country",
        ]
        records = data.get("transaction_history") or []
        frame = pd.DataFrame(records) if len(records) else pd.DataFrame(columns=columns)
        for column in columns:
            if column not in frame.columns:
                frame[column] = None
        frame["timestamp"] = pd.to_datetime(
            frame["timestamp"], utc=True, errors="coerce"
        )
        frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
        frame = frame.dropna(subset=["timestamp", "amount"])
        return frame.sort_values("timestamp").reset_index(drop=True)[columns]

    def _credit(self, data: Dict[str, Any], tx: pd.DataFrame) -> List[RiskFactor]:
        category = RiskCategory.CREDIT_RISK
        payments = data.get("payment_history") or []
        factors: List[RiskFactor] = []
        if payments:
            late = sum(
                1
                for p in payments
                if str(p.get("status", "")).lower() in {"late", "failed", "missed"}
            )
            ratio = late / len(payments)
            score = _clip(ratio * 2.0)
            description = f"{late} of {len(payments)} payments were late or failed"
        else:
            score, description = 0.5, "No payment history available"
        factors.append(
            RiskFactor(
                "payment_history",
                category,
                0.4,
                score,
                description,
                "high" if score >= 0.6 else "medium" if score >= 0.3 else "low",
                (
                    ["Enable automatic payments", "Settle overdue payments"]
                    if score >= 0.3
                    else []
                ),
            )
        )
        age = data.get("account_age_days")
        if age is None:
            age_score, age_desc = 0.5, "Account age unknown"
        else:
            age_score = _clip(1.0 - float(age) / 730.0)
            age_desc = f"Account is {int(age)} days old"
        factors.append(
            RiskFactor(
                "account_age",
                category,
                0.2,
                age_score,
                age_desc,
                "medium" if age_score >= 0.5 else "low",
                [],
            )
        )
        balances = data.get("account_balances") or {}
        limit = float(balances.get("credit_limit") or 0)
        used = float(balances.get("credit_used") or 0)
        if limit > 0:
            utilization = used / limit
            util_score = _clip((utilization - 0.3) / 0.7)
            util_desc = f"Credit utilization is {utilization:.0%}"
        else:
            util_score, util_desc = 0.3, "No credit line in use"
        factors.append(
            RiskFactor(
                "credit_utilization",
                category,
                0.2,
                util_score,
                util_desc,
                "high" if util_score >= 0.6 else "low",
                ["Reduce outstanding balances"] if util_score >= 0.6 else [],
            )
        )
        credit_rows = (
            tx[tx["type"].astype(str).str.lower().isin(["credit", "deposit", "income"])]
            if not tx.empty
            else tx
        )
        if len(credit_rows) >= 3:
            monthly = credit_rows.set_index("timestamp")["amount"].resample("30D").sum()
            monthly = monthly[monthly > 0]
            variation = (
                float(monthly.std(ddof=0) / monthly.mean())
                if len(monthly) >= 2 and monthly.mean() > 0
                else 0.0
            )
            stability = _clip(variation)
            desc = f"Income variation coefficient is {variation:.2f}"
        else:
            stability, desc = 0.5, "Insufficient income history"
        factors.append(
            RiskFactor(
                "income_stability",
                category,
                0.2,
                stability,
                desc,
                "medium" if stability >= 0.5 else "low",
                [],
            )
        )
        return factors

    def _fraud(self, data: Dict[str, Any], tx: pd.DataFrame) -> List[RiskFactor]:
        category = RiskCategory.FRAUD_RISK
        factors: List[RiskFactor] = []
        scores = [
            float(s) for s in (data.get("fraud_alert_scores") or []) if s is not None
        ]
        if scores:
            peak = max(scores)
            mean = float(np.mean(scores))
            model_score = _clip(0.6 * peak + 0.4 * mean)
            desc = f"Recent fraud model scores peak at {peak:.2f}"
        else:
            model_score, desc = 0.2, "No recent fraud model scores"
        factors.append(
            RiskFactor(
                "fraud_model_scores",
                category,
                0.35,
                model_score,
                desc,
                "high" if model_score >= 0.6 else "low",
                ["Review flagged transactions"] if model_score >= 0.6 else [],
            )
        )
        if not tx.empty:
            devices = tx["device_fingerprint"].dropna().astype(str)
            device_score = _clip((devices.nunique() - 1) / 4.0) if len(devices) else 0.2
            countries = tx["location_country"].dropna().astype(str)
            location_score = (
                _clip((countries.nunique() - 1) / 4.0) if len(countries) else 0.2
            )
            recent = tx[
                tx["timestamp"] > datetime.now(timezone.utc) - timedelta(hours=24)
            ]
            velocity_score = _clip(len(recent) / 30.0)
            amounts = tx["amount"].astype(float)
            mean, std = float(amounts.mean()), float(amounts.std(ddof=0))
            outliers = (
                float(((amounts - mean).abs() > 3 * std).mean()) if std > 0 else 0.0
            )
            behavior = _clip(outliers * 5.0)
        else:
            device_score = location_score = velocity_score = behavior = 0.3
        factors.extend(
            [
                RiskFactor(
                    "device_consistency",
                    category,
                    0.2,
                    device_score,
                    "Variety of devices used",
                    "medium" if device_score >= 0.5 else "low",
                    ["Enable device verification"] if device_score >= 0.5 else [],
                ),
                RiskFactor(
                    "location_patterns",
                    category,
                    0.2,
                    location_score,
                    "Variety of transaction countries",
                    "medium" if location_score >= 0.5 else "low",
                    [],
                ),
                RiskFactor(
                    "velocity_patterns",
                    category,
                    0.15,
                    velocity_score,
                    "Transactions in the last 24 hours",
                    "medium" if velocity_score >= 0.5 else "low",
                    [],
                ),
                RiskFactor(
                    "behavioral_anomalies",
                    category,
                    0.1,
                    behavior,
                    "Share of statistical outlier amounts",
                    "medium" if behavior >= 0.5 else "low",
                    [],
                ),
            ]
        )
        return factors

    def _liquidity(self, data: Dict[str, Any], tx: pd.DataFrame) -> List[RiskFactor]:
        category = RiskCategory.LIQUIDITY_RISK
        balances = data.get("account_balances") or {}
        available = float(balances.get("available") or balances.get("total") or 0.0)
        outflow = (
            tx[
                tx["type"]
                .astype(str)
                .str.lower()
                .isin(["debit", "payment", "transfer", "withdrawal"])
            ]
            if not tx.empty
            else tx
        )
        monthly_out = 0.0
        volatility = 0.5
        if not outflow.empty:
            span_days = max(
                (outflow["timestamp"].max() - outflow["timestamp"].min()).days, 1
            )
            monthly_out = float(outflow["amount"].sum()) / span_days * 30.0
            weekly = outflow.set_index("timestamp")["amount"].resample("7D").sum()
            if len(weekly) >= 3 and weekly.mean() > 0:
                volatility = _clip(float(weekly.std(ddof=0) / weekly.mean()) / 1.5)
        if monthly_out > 0:
            runway = available / monthly_out
            balance_score = _clip(1.0 - runway / 3.0)
            desc = f"Balance covers {runway:.1f} months of spending"
        else:
            balance_score, desc = (
                (0.3, "No spending baseline available")
                if available > 0
                else (0.5, "No balance information")
            )
        return [
            RiskFactor(
                "account_balances",
                category,
                0.5,
                balance_score,
                desc,
                "high" if balance_score >= 0.6 else "low",
                ["Build an emergency reserve"] if balance_score >= 0.6 else [],
            ),
            RiskFactor(
                "spending_volatility",
                category,
                0.5,
                volatility,
                "Weekly spending variability",
                "medium" if volatility >= 0.5 else "low",
                [],
            ),
        ]

    def _operational(self, data: Dict[str, Any], tx: pd.DataFrame) -> List[RiskFactor]:
        category = RiskCategory.OPERATIONAL_RISK
        incidents = data.get("security_incidents") or []
        incident_score = _clip(len(incidents) / 5.0)
        failed = 0
        if not tx.empty:
            failed = int(
                tx["status"]
                .astype(str)
                .str.lower()
                .isin(["failed", "reversed", "cancelled"])
                .sum()
            )
        error_score = _clip(failed / max(len(tx), 1) * 4.0) if not tx.empty else 0.2
        return [
            RiskFactor(
                "security_incidents",
                category,
                0.6,
                incident_score,
                f"{len(incidents)} security incidents recorded",
                "high" if incident_score >= 0.6 else "low",
                (
                    ["Rotate credentials", "Enable multi factor authentication"]
                    if incident_score >= 0.4
                    else []
                ),
            ),
            RiskFactor(
                "error_rates",
                category,
                0.4,
                error_score,
                "Share of failed or reversed transactions",
                "medium" if error_score >= 0.5 else "low",
                [],
            ),
        ]

    def _compliance(self, data: Dict[str, Any], tx: pd.DataFrame) -> List[RiskFactor]:
        category = RiskCategory.COMPLIANCE_RISK
        kyc = str(data.get("kyc_status", "not_started")).lower()
        kyc_score = KYC_SCORES.get(kyc, 0.6)
        records = data.get("compliance_records") or []
        violations = sum(
            1
            for r in records
            if str(r.get("status", "")).lower() in {"violation", "failed", "flagged"}
        )
        violation_score = _clip(violations / 3.0)
        return [
            RiskFactor(
                "kyc_status",
                category,
                0.5,
                kyc_score,
                f"KYC status is {kyc}",
                "high" if kyc_score >= 0.7 else "low",
                ["Complete identity verification"] if kyc_score >= 0.5 else [],
            ),
            RiskFactor(
                "compliance_violations",
                category,
                0.5,
                violation_score,
                f"{violations} compliance flags",
                "high" if violation_score >= 0.6 else "low",
                ["Resolve open compliance reviews"] if violations else [],
            ),
        ]

    @staticmethod
    def _category_score(factors: List[RiskFactor]) -> float:
        total = sum(f.weight for f in factors)
        if not total:
            return 0.5
        return _clip(sum(f.score * f.weight for f in factors) / total)

    @staticmethod
    def _overall(category_scores: Dict[str, float]) -> float:
        total = 0.0
        score = 0.0
        for category, weight in CATEGORY_WEIGHTS.items():
            value = category_scores.get(category.value)
            if value is None:
                continue
            score += value * weight
            total += weight
        base = score / total if total else 0.5
        peak = max(category_scores.values()) if category_scores else 0.0
        return _clip(0.8 * base + 0.2 * peak)

    @staticmethod
    def _completeness(data: Dict[str, Any], tx: pd.DataFrame) -> Dict[str, bool]:
        return {
            "transactions": len(tx) >= 10,
            "payments": bool(data.get("payment_history")),
            "balances": bool(data.get("account_balances")),
            "account_age": data.get("account_age_days") is not None,
            "kyc": bool(data.get("kyc_status")),
            "fraud_scores": bool(data.get("fraud_alert_scores")),
        }

    @staticmethod
    def _confidence(completeness: Dict[str, bool], tx: pd.DataFrame) -> float:
        base = sum(completeness.values()) / max(len(completeness), 1)
        volume = _clip(len(tx) / 100.0)
        return _clip(0.25 + 0.55 * base + 0.2 * volume)

    @staticmethod
    def _predictions(
        data: Dict[str, Any], tx: pd.DataFrame, scores: Dict[str, float], overall: float
    ) -> Dict[str, Any]:
        trend = 0.0
        if not tx.empty and len(tx) >= 8:
            weekly = (
                tx.set_index("timestamp")["amount"]
                .resample("7D")
                .sum()
                .to_numpy(dtype=float)
            )
            if len(weekly) >= 3:
                slope = float(np.polyfit(np.arange(len(weekly)), weekly, 1)[0])
                mean = float(weekly.mean()) or 1.0
                trend = float(np.clip(slope / mean, -1.0, 1.0))
        return {
            "default_probability_90d": round(
                _logistic(scores.get("credit_risk", 0.5), 0.6, 8.0), 4
            ),
            "fraud_probability_30d": round(
                _logistic(scores.get("fraud_risk", 0.3), 0.55, 8.0), 4
            ),
            "liquidity_shortfall_probability_30d": round(
                _logistic(scores.get("liquidity_risk", 0.5), 0.6, 8.0), 4
            ),
            "spending_trend": round(trend, 4),
            "projected_risk_score_30d": round(
                _clip(overall + 0.1 * max(trend, 0.0)), 4
            ),
        }

    @staticmethod
    def _recommendations(factors: List[RiskFactor], level: RiskTier) -> List[str]:
        ranked = sorted(factors, key=lambda f: f.score * f.weight, reverse=True)
        recommendations: List[str] = []
        for factor in ranked:
            for suggestion in factor.mitigation_suggestions:
                if suggestion not in recommendations and factor.score >= 0.4:
                    recommendations.append(suggestion)
        if level in (RiskTier.HIGH, RiskTier.VERY_HIGH, RiskTier.CRITICAL):
            recommendations.insert(0, "Escalate for manual risk review")
        if not recommendations:
            recommendations.append("Continue standard monitoring")
        return recommendations[:8]

    @staticmethod
    def _alerts(factors: List[RiskFactor], predictions: Dict[str, Any]) -> List[str]:
        alerts = [
            f"{f.factor_name}: {f.description}" for f in factors if f.score >= 0.7
        ]
        if predictions.get("fraud_probability_30d", 0) >= 0.6:
            alerts.append("Elevated 30 day fraud probability")
        if predictions.get("default_probability_90d", 0) >= 0.6:
            alerts.append("Elevated 90 day default probability")
        return alerts

    @staticmethod
    def _assessment_id(user_id: str) -> str:
        digest = hashlib.sha256(f"{user_id}:{uuid.uuid4()}".encode("utf-8")).hexdigest()
        return f"risk-{digest[:16]}"

    def generate_risk_report(
        self, user_id: str, user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        assessment = self.assess_user_risk(user_id, user_data=user_data)
        with self._lock:
            history = list(self._history[user_id])
        return {
            "assessment": assessment.to_dict(),
            "history": [
                {**item, "timestamp": item["timestamp"].isoformat()} for item in history
            ],
            "trend": self._trend(history),
        }

    @staticmethod
    def _trend(history: List[Dict[str, Any]]) -> str:
        if len(history) < 3:
            return "insufficient_data"
        scores = [item["score"] for item in history]
        slope = float(np.polyfit(np.arange(len(scores)), scores, 1)[0])
        if slope > 0.02:
            return "worsening"
        if slope < -0.02:
            return "improving"
        return "stable"


ai_risk_assessor = AIRiskAssessor()
