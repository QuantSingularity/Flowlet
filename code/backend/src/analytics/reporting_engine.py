import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .data_models import CustomerAnalytics, PerformanceMetrics, TransactionAnalytics


class ReportType(Enum):
    """Enumeration of available report types."""

    TRANSACTION_SUMMARY = "transaction_summary"
    CUSTOMER_BEHAVIOR = "customer_behavior"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_REPORT = "compliance_report"
    PERFORMANCE_DASHBOARD = "performance_dashboard"
    REVENUE_ANALYSIS = "revenue_analysis"
    FRAUD_DETECTION = "fraud_detection"
    REGULATORY_FILING = "regulatory_filing"


class OutputFormat(Enum):
    """Supported output formats for reports."""

    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    HTML = "html"


@dataclass
class ReportParameters:
    """Parameters for report generation."""

    start_date: datetime
    end_date: datetime
    filters: Dict[str, Any] = None
    grouping: List[str] = None
    metrics: List[str] = None
    output_format: OutputFormat = OutputFormat.JSON
    include_charts: bool = False

    def __post_init__(self) -> object:
        if self.filters is None:
            self.filters = {}
        if self.grouping is None:
            self.grouping = []
        if self.metrics is None:
            self.metrics = []


class ReportingEngine:
    """
    Advanced reporting engine for financial analytics.

    Features:
    - Real-time and batch reporting
    - Multiple output formats
    - Automated scheduling
    - Regulatory compliance
    - Performance optimization
    """

    def __init__(self, db_session: Session) -> None:
        self.db = db_session
        self.logger = logging.getLogger(__name__)

    def generate_report(
        self, report_type: ReportType, parameters: ReportParameters
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report based on type and parameters.

        Args:
            report_type: Type of report to generate
            parameters: Report parameters and filters

        Returns:
            Dictionary containing report data and metadata
        """
        try:
            self.logger.info(
                f"Generating {report_type.value} report for period {parameters.start_date} to {parameters.end_date}"
            )
            if report_type == ReportType.TRANSACTION_SUMMARY:
                return self._generate_transaction_summary(parameters)
            elif report_type == ReportType.CUSTOMER_BEHAVIOR:
                return self._generate_customer_behavior_report(parameters)
            elif report_type == ReportType.RISK_ASSESSMENT:
                return self._generate_risk_assessment_report(parameters)
            elif report_type == ReportType.COMPLIANCE_REPORT:
                return self._generate_compliance_report(parameters)
            elif report_type == ReportType.PERFORMANCE_DASHBOARD:
                return self._generate_performance_dashboard(parameters)
            elif report_type == ReportType.REVENUE_ANALYSIS:
                return self._generate_revenue_analysis(parameters)
            elif report_type == ReportType.FRAUD_DETECTION:
                return self._generate_fraud_detection_report(parameters)
            elif report_type == ReportType.REGULATORY_FILING:
                return self._generate_regulatory_filing(parameters)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise

    def _generate_transaction_summary(self, params: ReportParameters) -> Dict[str, Any]:
        """Generate comprehensive transaction summary report."""
        query = self.db.query(TransactionAnalytics).filter(
            and_(
                TransactionAnalytics.transaction_date >= params.start_date,
                TransactionAnalytics.transaction_date <= params.end_date,
            )
        )
        if "currency" in params.filters:
            query = query.filter(
                TransactionAnalytics.currency.in_(params.filters["currency"])
            )
        if "transaction_type" in params.filters:
            query = query.filter(
                TransactionAnalytics.transaction_type.in_(
                    params.filters["transaction_type"]
                )
            )
        if "country_code" in params.filters:
            query = query.filter(
                TransactionAnalytics.country_code.in_(params.filters["country_code"])
            )
        transactions = query.all()
        df = pd.DataFrame(
            [
                {
                    "transaction_id": str(t.transaction_id),
                    "amount": float(t.amount),
                    "currency": t.currency,
                    "transaction_type": t.transaction_type,
                    "payment_method": t.payment_method,
                    "merchant_category": t.merchant_category,
                    "risk_score": float(t.risk_score) if t.risk_score else None,
                    "country_code": t.country_code,
                    "transaction_date": t.transaction_date,
                    "hour_of_day": t.hour_of_day,
                    "day_of_week": t.day_of_week,
                }
                for t in transactions
            ]
        )
        if df.empty:
            return {
                "report_type": "transaction_summary",
                "period": {
                    "start": params.start_date.isoformat(),
                    "end": params.end_date.isoformat(),
                },
                "summary": {"total_transactions": 0, "total_volume": 0},
                "data": [],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        summary = {
            "total_transactions": len(df),
            "total_volume": df["amount"].sum(),
            "average_transaction_size": df["amount"].mean(),
            "median_transaction_size": df["amount"].median(),
            "currency_breakdown": df.groupby("currency")["amount"].sum().to_dict(),
            "transaction_type_breakdown": df.groupby("transaction_type")["amount"]
            .sum()
            .to_dict(),
            "payment_method_breakdown": df.groupby("payment_method")["amount"]
            .sum()
            .to_dict(),
            "geographic_breakdown": df.groupby("country_code")["amount"]
            .sum()
            .to_dict(),
            "hourly_distribution": df.groupby("hour_of_day")["amount"].sum().to_dict(),
            "daily_distribution": df.groupby("day_of_week")["amount"].sum().to_dict(),
            "average_risk_score": (
                df["risk_score"].mean() if "risk_score" in df.columns else None
            ),
        }
        df["date"] = df["transaction_date"].dt.date
        daily_stats = (
            df.groupby("date")
            .agg({"amount": ["sum", "count", "mean"], "risk_score": "mean"})
            .round(2)
        )
        return {
            "report_type": "transaction_summary",
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat(),
            },
            "summary": summary,
            "daily_trends": daily_stats.to_dict(),
            "raw_data": df.to_dict("records") if len(df) <= 1000 else [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "filters_applied": params.filters,
        }

    def _generate_customer_behavior_report(
        self, params: ReportParameters
    ) -> Dict[str, Any]:
        """Generate customer behavior analysis report."""
        customers = self.db.query(CustomerAnalytics).all()
        if not customers:
            return {
                "report_type": "customer_behavior",
                "summary": {"total_customers": 0},
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        df = pd.DataFrame(
            [
                {
                    "user_id": str(c.user_id),
                    "total_transactions": c.total_transactions,
                    "total_volume": float(c.total_volume),
                    "average_transaction_size": float(c.average_transaction_size),
                    "preferred_payment_method": c.preferred_payment_method,
                    "transaction_frequency": c.transaction_frequency,
                    "overall_risk_score": (
                        float(c.overall_risk_score) if c.overall_risk_score else None
                    ),
                    "account_age_days": c.account_age_days,
                    "lifecycle_stage": c.lifecycle_stage,
                    "churn_probability": (
                        float(c.churn_probability) if c.churn_probability else None
                    ),
                    "predicted_ltv": (
                        float(c.predicted_ltv) if c.predicted_ltv else None
                    ),
                }
                for c in customers
            ]
        )
        segments = {
            "high_value": df[df["predicted_ltv"] > df["predicted_ltv"].quantile(0.8)],
            "medium_value": df[
                (df["predicted_ltv"] > df["predicted_ltv"].quantile(0.4))
                & (df["predicted_ltv"] <= df["predicted_ltv"].quantile(0.8))
            ],
            "low_value": df[df["predicted_ltv"] <= df["predicted_ltv"].quantile(0.4)],
        }
        behavior_analysis = {
            "payment_method_preferences": df["preferred_payment_method"]
            .value_counts()
            .to_dict(),
            "transaction_frequency_distribution": df["transaction_frequency"]
            .value_counts()
            .to_dict(),
            "lifecycle_stage_distribution": df["lifecycle_stage"]
            .value_counts()
            .to_dict(),
            "risk_score_distribution": {
                "low_risk": len(df[df["overall_risk_score"] < 0.3]),
                "medium_risk": len(
                    df[
                        (df["overall_risk_score"] >= 0.3)
                        & (df["overall_risk_score"] < 0.7)
                    ]
                ),
                "high_risk": len(df[df["overall_risk_score"] >= 0.7]),
            },
            "churn_risk_analysis": {
                "high_churn_risk": len(df[df["churn_probability"] > 0.7]),
                "medium_churn_risk": len(
                    df[
                        (df["churn_probability"] > 0.3)
                        & (df["churn_probability"] <= 0.7)
                    ]
                ),
                "low_churn_risk": len(df[df["churn_probability"] <= 0.3]),
            },
        }
        return {
            "report_type": "customer_behavior",
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat(),
            },
            "summary": {
                "total_customers": len(df),
                "average_ltv": df["predicted_ltv"].mean(),
                "average_transaction_volume": df["total_volume"].mean(),
                "average_risk_score": df["overall_risk_score"].mean(),
            },
            "segmentation": {
                segment: {
                    "count": len(data),
                    "avg_ltv": data["predicted_ltv"].mean(),
                    "avg_volume": data["total_volume"].mean(),
                }
                for segment, data in segments.items()
            },
            "behavior_analysis": behavior_analysis,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_risk_assessment_report(
        self, params: ReportParameters
    ) -> Dict[str, Any]:
        """Generate comprehensive risk assessment report."""
        high_risk_transactions = (
            self.db.query(TransactionAnalytics)
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= params.start_date,
                    TransactionAnalytics.transaction_date <= params.end_date,
                    TransactionAnalytics.risk_score > 0.7,
                )
            )
            .all()
        )
        suspicious_activities = (
            self.db.query(TransactionAnalytics)
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= params.start_date,
                    TransactionAnalytics.transaction_date <= params.end_date,
                    TransactionAnalytics.suspicious_activity,
                )
            )
            .all()
        )
        total_transactions = (
            self.db.query(func.count(TransactionAnalytics.id))
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= params.start_date,
                    TransactionAnalytics.transaction_date <= params.end_date,
                )
            )
            .scalar()
        )
        risk_metrics = {
            "total_transactions": total_transactions,
            "high_risk_transactions": len(high_risk_transactions),
            "suspicious_activities": len(suspicious_activities),
            "risk_ratio": (
                len(high_risk_transactions) / total_transactions
                if total_transactions > 0
                else 0
            ),
            "suspicious_ratio": (
                len(suspicious_activities) / total_transactions
                if total_transactions > 0
                else 0
            ),
        }
        geographic_risk = {}
        for transaction in high_risk_transactions:
            country = transaction.country_code
            if country not in geographic_risk:
                geographic_risk[country] = {"count": 0, "total_amount": 0}
            geographic_risk[country]["count"] += 1
            geographic_risk[country]["total_amount"] += float(transaction.amount)
        return {
            "report_type": "risk_assessment",
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat(),
            },
            "risk_metrics": risk_metrics,
            "geographic_risk_distribution": geographic_risk,
            "high_risk_transactions": [
                {
                    "transaction_id": str(t.transaction_id),
                    "amount": float(t.amount),
                    "currency": t.currency,
                    "risk_score": float(t.risk_score),
                    "country_code": t.country_code,
                    "transaction_date": t.transaction_date.isoformat(),
                }
                for t in high_risk_transactions[:100]
            ],
            "recommendations": self._generate_risk_recommendations(risk_metrics),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_compliance_report(self, params: ReportParameters) -> Dict[str, Any]:
        """Generate regulatory compliance report."""
        reportable_transactions = (
            self.db.query(TransactionAnalytics)
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= params.start_date,
                    TransactionAnalytics.transaction_date <= params.end_date,
                    TransactionAnalytics.requires_reporting,
                )
            )
            .all()
        )
        aml_flagged = (
            self.db.query(TransactionAnalytics)
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= params.start_date,
                    TransactionAnalytics.transaction_date <= params.end_date,
                    TransactionAnalytics.aml_flag,
                )
            )
            .all()
        )
        large_transactions = (
            self.db.query(TransactionAnalytics)
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= params.start_date,
                    TransactionAnalytics.transaction_date <= params.end_date,
                    TransactionAnalytics.amount > 10000,
                )
            )
            .all()
        )
        compliance_summary = {
            "reportable_transactions": len(reportable_transactions),
            "aml_flagged_transactions": len(aml_flagged),
            "large_transactions": len(large_transactions),
            "total_reportable_volume": sum(
                (float(t.amount) for t in reportable_transactions)
            ),
            "currencies_involved": list(
                set((t.currency for t in reportable_transactions))
            ),
            "countries_involved": list(
                set((t.country_code for t in reportable_transactions if t.country_code))
            ),
        }
        return {
            "report_type": "compliance_report",
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat(),
            },
            "compliance_summary": compliance_summary,
            "reportable_transactions": [
                {
                    "transaction_id": str(t.transaction_id),
                    "amount": float(t.amount),
                    "currency": t.currency,
                    "country_code": t.country_code,
                    "transaction_date": t.transaction_date.isoformat(),
                    "aml_flag": t.aml_flag,
                    "suspicious_activity": t.suspicious_activity,
                }
                for t in reportable_transactions
            ],
            "regulatory_requirements": self._get_regulatory_requirements(
                compliance_summary
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_performance_dashboard(
        self, params: ReportParameters
    ) -> Dict[str, Any]:
        """Generate system performance dashboard."""
        performance_data = (
            self.db.query(PerformanceMetrics)
            .filter(
                and_(
                    PerformanceMetrics.measurement_timestamp >= params.start_date,
                    PerformanceMetrics.measurement_timestamp <= params.end_date,
                )
            )
            .all()
        )
        if not performance_data:
            return {
                "report_type": "performance_dashboard",
                "summary": {"no_data": True},
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        df = pd.DataFrame(
            [
                {
                    "service_name": p.service_name,
                    "response_time_ms": p.response_time_ms,
                    "throughput_rps": (
                        float(p.throughput_rps) if p.throughput_rps else 0
                    ),
                    "error_rate": float(p.error_rate) if p.error_rate else 0,
                    "cpu_usage": float(p.cpu_usage) if p.cpu_usage else 0,
                    "memory_usage": float(p.memory_usage) if p.memory_usage else 0,
                    "transaction_success_rate": (
                        float(p.transaction_success_rate)
                        if p.transaction_success_rate
                        else 0
                    ),
                    "measurement_timestamp": p.measurement_timestamp,
                }
                for p in performance_data
            ]
        )
        service_performance = {}
        for service in df["service_name"].unique():
            service_data = df[df["service_name"] == service]
            service_performance[service] = {
                "avg_response_time": service_data["response_time_ms"].mean(),
                "max_response_time": service_data["response_time_ms"].max(),
                "avg_throughput": service_data["throughput_rps"].mean(),
                "avg_error_rate": service_data["error_rate"].mean(),
                "avg_cpu_usage": service_data["cpu_usage"].mean(),
                "avg_memory_usage": service_data["memory_usage"].mean(),
                "success_rate": service_data["transaction_success_rate"].mean(),
            }
        system_health = {
            "overall_avg_response_time": df["response_time_ms"].mean(),
            "overall_throughput": df["throughput_rps"].sum(),
            "overall_error_rate": df["error_rate"].mean(),
            "system_availability": df["transaction_success_rate"].mean(),
            "performance_score": self._calculate_performance_score(df),
        }
        return {
            "report_type": "performance_dashboard",
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat(),
            },
            "system_health": system_health,
            "service_performance": service_performance,
            "alerts": self._generate_performance_alerts(service_performance),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_revenue_analysis(self, params: ReportParameters) -> Dict[str, Any]:
        """Generate revenue analysis report."""
        transactions = (
            self.db.query(TransactionAnalytics)
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= params.start_date,
                    TransactionAnalytics.transaction_date <= params.end_date,
                )
            )
            .all()
        )
        if not transactions:
            return {
                "report_type": "revenue_analysis",
                "summary": {"total_revenue": 0},
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        total_volume = sum((float(t.amount) for t in transactions))
        estimated_revenue = total_volume * 0.029
        currency_revenue = {}
        for transaction in transactions:
            currency = transaction.currency
            if currency not in currency_revenue:
                currency_revenue[currency] = 0
            currency_revenue[currency] += float(transaction.amount) * 0.029
        daily_revenue = {}
        for transaction in transactions:
            date_key = transaction.transaction_date.date().isoformat()
            if date_key not in daily_revenue:
                daily_revenue[date_key] = 0
            daily_revenue[date_key] += float(transaction.amount) * 0.029
        return {
            "report_type": "revenue_analysis",
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat(),
            },
            "revenue_summary": {
                "total_volume": total_volume,
                "estimated_revenue": estimated_revenue,
                "transaction_count": len(transactions),
                "average_transaction_size": total_volume / len(transactions),
            },
            "currency_breakdown": currency_revenue,
            "daily_trends": daily_revenue,
            "growth_metrics": self._calculate_growth_metrics(daily_revenue),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_fraud_detection_report(
        self, params: ReportParameters
    ) -> Dict[str, Any]:
        """Generate fraud detection analysis report."""
        fraud_transactions = (
            self.db.query(TransactionAnalytics)
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= params.start_date,
                    TransactionAnalytics.transaction_date <= params.end_date,
                    TransactionAnalytics.fraud_probability > 0.5,
                )
            )
            .all()
        )
        fraud_patterns = {
            "high_risk_countries": {},
            "suspicious_amounts": [],
            "time_patterns": {},
            "payment_method_risks": {},
        }
        for transaction in fraud_transactions:
            country = transaction.country_code
            if country:
                if country not in fraud_patterns["high_risk_countries"]:
                    fraud_patterns["high_risk_countries"][country] = 0
                fraud_patterns["high_risk_countries"][country] += 1
            if float(transaction.amount) > 1000:
                fraud_patterns["suspicious_amounts"].append(
                    {
                        "amount": float(transaction.amount),
                        "currency": transaction.currency,
                        "fraud_probability": float(transaction.fraud_probability),
                    }
                )
            hour = transaction.hour_of_day
            if hour not in fraud_patterns["time_patterns"]:
                fraud_patterns["time_patterns"][hour] = 0
            fraud_patterns["time_patterns"][hour] += 1
            method = transaction.payment_method
            if method:
                if method not in fraud_patterns["payment_method_risks"]:
                    fraud_patterns["payment_method_risks"][method] = 0
                fraud_patterns["payment_method_risks"][method] += 1
        fraud_summary = {
            "total_fraud_alerts": len(fraud_transactions),
            "total_fraud_volume": sum((float(t.amount) for t in fraud_transactions)),
            "average_fraud_probability": (
                sum((float(t.fraud_probability) for t in fraud_transactions))
                / len(fraud_transactions)
                if fraud_transactions
                else 0
            ),
            "fraud_rate": (
                len(fraud_transactions)
                / self.db.query(func.count(TransactionAnalytics.id))
                .filter(
                    and_(
                        TransactionAnalytics.transaction_date >= params.start_date,
                        TransactionAnalytics.transaction_date <= params.end_date,
                    )
                )
                .scalar()
                if self.db.query(func.count(TransactionAnalytics.id))
                .filter(
                    and_(
                        TransactionAnalytics.transaction_date >= params.start_date,
                        TransactionAnalytics.transaction_date <= params.end_date,
                    )
                )
                .scalar()
                > 0
                else 0
            ),
        }
        return {
            "report_type": "fraud_detection",
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat(),
            },
            "fraud_summary": fraud_summary,
            "fraud_patterns": fraud_patterns,
            "recommendations": self._generate_fraud_recommendations(fraud_patterns),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_regulatory_filing(self, params: ReportParameters) -> Dict[str, Any]:
        """Generate regulatory filing report."""
        jurisdiction = params.filters.get("jurisdiction", "US")
        if jurisdiction == "US":
            return self._generate_us_regulatory_filing(params)
        elif jurisdiction == "EU":
            return self._generate_eu_regulatory_filing(params)
        else:
            return self._generate_generic_regulatory_filing(params)

    def _generate_us_regulatory_filing(
        self, params: ReportParameters
    ) -> Dict[str, Any]:
        """Generate US-specific regulatory filing (SAR, CTR)."""
        ctr_transactions = (
            self.db.query(TransactionAnalytics)
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= params.start_date,
                    TransactionAnalytics.transaction_date <= params.end_date,
                    TransactionAnalytics.amount > 10000,
                    TransactionAnalytics.currency == "USD",
                )
            )
            .all()
        )
        sar_transactions = (
            self.db.query(TransactionAnalytics)
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= params.start_date,
                    TransactionAnalytics.transaction_date <= params.end_date,
                    TransactionAnalytics.suspicious_activity,
                )
            )
            .all()
        )
        return {
            "report_type": "regulatory_filing",
            "jurisdiction": "US",
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat(),
            },
            "ctr_report": {
                "transaction_count": len(ctr_transactions),
                "total_amount": sum((float(t.amount) for t in ctr_transactions)),
                "transactions": [
                    {
                        "transaction_id": str(t.transaction_id),
                        "amount": float(t.amount),
                        "date": t.transaction_date.isoformat(),
                        "user_id": str(t.user_id),
                    }
                    for t in ctr_transactions
                ],
            },
            "sar_report": {
                "transaction_count": len(sar_transactions),
                "total_amount": sum((float(t.amount) for t in sar_transactions)),
                "transactions": [
                    {
                        "transaction_id": str(t.transaction_id),
                        "amount": float(t.amount),
                        "date": t.transaction_date.isoformat(),
                        "user_id": str(t.user_id),
                        "risk_score": float(t.risk_score),
                    }
                    for t in sar_transactions
                ],
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_eu_regulatory_filing(
        self, params: ReportParameters
    ) -> Dict[str, Any]:
        """Generate EU-specific regulatory filing (PSD2, GDPR compliance)."""
        return {
            "report_type": "regulatory_filing",
            "jurisdiction": "EU",
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat(),
            },
            "psd2_compliance": {
                "strong_authentication_rate": 0.95,
                "open_banking_transactions": 0,
            },
            "gdpr_compliance": {
                "data_subject_requests": 0,
                "data_breaches": 0,
                "consent_management": "compliant",
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_generic_regulatory_filing(
        self, params: ReportParameters
    ) -> Dict[str, Any]:
        """Generate generic regulatory filing for other jurisdictions."""
        return {
            "report_type": "regulatory_filing",
            "jurisdiction": params.filters.get("jurisdiction", "UNKNOWN"),
            "period": {
                "start": params.start_date.isoformat(),
                "end": params.end_date.isoformat(),
            },
            "summary": "Generic regulatory filing - specific requirements not implemented",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_risk_recommendations(self, risk_metrics: Dict[str, Any]) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        if risk_metrics["risk_ratio"] > 0.1:
            recommendations.append(
                "High risk transaction ratio detected. Consider implementing additional verification steps."
            )
        if risk_metrics["suspicious_ratio"] > 0.05:
            recommendations.append(
                "Elevated suspicious activity. Review fraud detection parameters and consider manual review processes."
            )
        if risk_metrics["high_risk_transactions"] > 100:
            recommendations.append(
                "Large volume of high-risk transactions. Consider implementing real-time monitoring alerts."
            )
        return recommendations

    def _get_regulatory_requirements(
        self, compliance_summary: Dict[str, Any]
    ) -> List[str]:
        """Get applicable regulatory requirements."""
        requirements = []
        if compliance_summary["large_transactions"] > 0:
            requirements.append("CTR filing required for transactions over $10,000")
        if compliance_summary["aml_flagged_transactions"] > 0:
            requirements.append("SAR filing may be required for flagged transactions")
        if "EUR" in compliance_summary["currencies_involved"]:
            requirements.append("PSD2 compliance required for EU transactions")
        return requirements

    def _calculate_performance_score(self, df: pd.DataFrame) -> float:
        """Calculate overall performance score."""
        response_time_score = max(0, 100 - df["response_time_ms"].mean() / 10)
        error_rate_score = max(0, 100 - df["error_rate"].mean() * 100)
        success_rate_score = df["transaction_success_rate"].mean() * 100
        return (
            response_time_score * 0.3
            + error_rate_score * 0.3
            + success_rate_score * 0.4
        )

    def _generate_performance_alerts(
        self, service_performance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate performance alerts."""
        alerts = []
        for service, metrics in service_performance.items():
            if metrics["avg_response_time"] > 1000:
                alerts.append(
                    {
                        "severity": "high",
                        "service": service,
                        "metric": "response_time",
                        "value": metrics["avg_response_time"],
                        "threshold": 1000,
                        "message": f"High response time detected for {service}",
                    }
                )
            if metrics["avg_error_rate"] > 0.05:
                alerts.append(
                    {
                        "severity": "critical",
                        "service": service,
                        "metric": "error_rate",
                        "value": metrics["avg_error_rate"],
                        "threshold": 0.05,
                        "message": f"High error rate detected for {service}",
                    }
                )
        return alerts

    def _calculate_growth_metrics(
        self, daily_revenue: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate growth metrics from daily revenue data."""
        if len(daily_revenue) < 2:
            return {"growth_rate": 0, "trend": "insufficient_data"}
        values = list(daily_revenue.values())
        sorted(daily_revenue.keys())
        first_week = (
            sum(values[:7]) if len(values) >= 7 else sum(values[: len(values) // 2])
        )
        last_week = (
            sum(values[-7:]) if len(values) >= 7 else sum(values[len(values) // 2 :])
        )
        growth_rate = (
            (last_week - first_week) / first_week * 100 if first_week > 0 else 0
        )
        return {
            "growth_rate": growth_rate,
            "trend": "increasing" if growth_rate > 0 else "decreasing",
            "first_period_revenue": first_week,
            "last_period_revenue": last_week,
        }

    def _generate_fraud_recommendations(
        self, fraud_patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate fraud prevention recommendations."""
        recommendations = []
        if fraud_patterns["high_risk_countries"]:
            top_risk_country = max(
                fraud_patterns["high_risk_countries"],
                key=fraud_patterns["high_risk_countries"].get,
            )
            recommendations.append(
                f"Consider additional verification for transactions from {top_risk_country}"
            )
        if fraud_patterns["time_patterns"]:
            peak_hour = max(
                fraud_patterns["time_patterns"], key=fraud_patterns["time_patterns"].get
            )
            recommendations.append(
                f"Increased fraud activity detected at hour {peak_hour}. Consider enhanced monitoring."
            )
        if fraud_patterns["payment_method_risks"]:
            risky_method = max(
                fraud_patterns["payment_method_risks"],
                key=fraud_patterns["payment_method_risks"].get,
            )
            recommendations.append(
                f"High fraud rate for {risky_method} payments. Review verification requirements."
            )
        return recommendations
