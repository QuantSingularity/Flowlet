import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .data_models import CustomerAnalytics, PerformanceMetrics, TransactionAnalytics


class MetricType(Enum):
    """Types of metrics that can be calculated."""

    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    RISK = "risk"
    CUSTOMER = "customer"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"


class AggregationType(Enum):
    """Types of aggregation for metrics."""

    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    STANDARD_DEVIATION = "std_dev"
    VARIANCE = "variance"


@dataclass
class MetricDefinition:
    """Definition of a metric calculation."""

    name: str
    type: MetricType
    description: str
    calculation_method: str
    aggregation: AggregationType
    data_source: str
    filters: Dict[str, Any] = None
    parameters: Dict[str, Any] = None

    def __post_init__(self) -> object:
        if self.filters is None:
            self.filters = {}
        if self.parameters is None:
            self.parameters = {}


@dataclass
class MetricResult:
    """Result of a metric calculation."""

    metric_name: str
    value: float
    previous_value: Optional[float]
    change_percentage: Optional[float]
    calculation_timestamp: datetime
    period_start: datetime
    period_end: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> object:
        if self.metadata is None:
            self.metadata = {}


class MetricsCalculator:
    """
    Advanced metrics calculation engine for financial analytics.

    Features:
    - Real-time metric calculation
    - Historical trend analysis
    - Comparative analysis
    - Automated alerting
    - Performance optimization
    """

    def __init__(self, db_session: Session) -> None:
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self._metric_definitions = self._load_default_metrics()
        self._calculation_cache = {}

    def calculate_metric(
        self,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        filters: Dict[str, Any] = None,
    ) -> MetricResult:
        """
        Calculate a specific metric for the given time period.

        Args:
            metric_name: Name of the metric to calculate
            start_date: Start of the calculation period
            end_date: End of the calculation period
            filters: Additional filters to apply

        Returns:
            MetricResult containing the calculated value and metadata
        """
        if metric_name not in self._metric_definitions:
            raise ValueError(f"Unknown metric: {metric_name}")
        metric_def = self._metric_definitions[metric_name]
        combined_filters = {**metric_def.filters}
        if filters:
            combined_filters.update(filters)
        try:
            current_value = self._calculate_metric_value(
                metric_def, start_date, end_date, combined_filters
            )
            period_duration = end_date - start_date
            prev_start = start_date - period_duration
            prev_end = start_date
            previous_value = self._calculate_metric_value(
                metric_def, prev_start, prev_end, combined_filters
            )
            change_percentage = None
            if previous_value and previous_value != 0:
                change_percentage = (
                    (current_value - previous_value) / previous_value * 100
                )
            result = MetricResult(
                metric_name=metric_name,
                value=current_value,
                previous_value=previous_value,
                change_percentage=change_percentage,
                calculation_timestamp=datetime.now(timezone.utc),
                period_start=start_date,
                period_end=end_date,
                metadata={
                    "metric_type": metric_def.type.value,
                    "aggregation": metric_def.aggregation.value,
                    "filters_applied": combined_filters,
                },
            )
            self.logger.info(f"Calculated metric {metric_name}: {current_value}")
            return result
        except Exception as e:
            self.logger.error(f"Error calculating metric {metric_name}: {str(e)}")
            raise

    def calculate_multiple_metrics(
        self,
        metric_names: List[str],
        start_date: datetime,
        end_date: datetime,
        filters: Dict[str, Any] = None,
    ) -> List[MetricResult]:
        """Calculate multiple metrics in batch."""
        results = []
        for metric_name in metric_names:
            try:
                result = self.calculate_metric(
                    metric_name, start_date, end_date, filters
                )
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error calculating metric {metric_name}: {str(e)}")
        return results

    def _calculate_metric_value(
        self,
        metric_def: MetricDefinition,
        start_date: datetime,
        end_date: datetime,
        filters: Dict[str, Any],
    ) -> float:
        """Calculate the actual metric value based on definition."""
        if metric_def.data_source == "transactions":
            return self._calculate_transaction_metric(
                metric_def, start_date, end_date, filters
            )
        elif metric_def.data_source == "customers":
            return self._calculate_customer_metric(
                metric_def, start_date, end_date, filters
            )
        elif metric_def.data_source == "performance":
            return self._calculate_performance_metric(
                metric_def, start_date, end_date, filters
            )
        else:
            raise ValueError(f"Unknown data source: {metric_def.data_source}")

    def _calculate_transaction_metric(
        self,
        metric_def: MetricDefinition,
        start_date: datetime,
        end_date: datetime,
        filters: Dict[str, Any],
    ) -> float:
        """Calculate metrics based on transaction data."""
        query = self.db.query(TransactionAnalytics).filter(
            and_(
                TransactionAnalytics.transaction_date >= start_date,
                TransactionAnalytics.transaction_date <= end_date,
            )
        )
        if "currency" in filters:
            query = query.filter(TransactionAnalytics.currency.in_(filters["currency"]))
        if "transaction_type" in filters:
            query = query.filter(
                TransactionAnalytics.transaction_type.in_(filters["transaction_type"])
            )
        if "country_code" in filters:
            query = query.filter(
                TransactionAnalytics.country_code.in_(filters["country_code"])
            )
        if "min_amount" in filters:
            query = query.filter(TransactionAnalytics.amount >= filters["min_amount"])
        if "max_amount" in filters:
            query = query.filter(TransactionAnalytics.amount <= filters["max_amount"])
        if metric_def.name == "total_transaction_count":
            return float(query.count())
        elif metric_def.name == "total_transaction_volume":
            result = query.with_entities(func.sum(TransactionAnalytics.amount)).scalar()
            return float(result) if result else 0.0
        elif metric_def.name == "average_transaction_amount":
            result = query.with_entities(func.avg(TransactionAnalytics.amount)).scalar()
            return float(result) if result else 0.0
        elif metric_def.name == "median_transaction_amount":
            amounts = [float(t.amount) for t in query.all()]
            return float(np.median(amounts)) if amounts else 0.0
        elif metric_def.name == "transaction_volume_growth_rate":
            current_volume = query.with_entities(
                func.sum(TransactionAnalytics.amount)
            ).scalar()
            return float(current_volume) if current_volume else 0.0
        elif metric_def.name == "high_risk_transaction_ratio":
            total_count = query.count()
            high_risk_count = query.filter(
                TransactionAnalytics.risk_score > 0.7
            ).count()
            return high_risk_count / total_count if total_count > 0 else 0.0
        elif metric_def.name == "fraud_detection_rate":
            total_count = query.count()
            fraud_count = query.filter(
                TransactionAnalytics.fraud_probability > 0.5
            ).count()
            return fraud_count / total_count if total_count > 0 else 0.0
        elif metric_def.name == "average_risk_score":
            result = query.with_entities(
                func.avg(TransactionAnalytics.risk_score)
            ).scalar()
            return float(result) if result else 0.0
        elif metric_def.name == "cross_border_transaction_ratio":
            total_count = query.count()
            cross_border_count = query.filter(
                TransactionAnalytics.country_code.notin_(["US", "domestic"])
            ).count()
            return cross_border_count / total_count if total_count > 0 else 0.0
        elif metric_def.name == "large_transaction_count":
            return float(query.filter(TransactionAnalytics.amount > 10000).count())
        elif metric_def.name == "suspicious_activity_ratio":
            total_count = query.count()
            suspicious_count = query.filter(
                TransactionAnalytics.suspicious_activity
            ).count()
            return suspicious_count / total_count if total_count > 0 else 0.0
        elif metric_def.name == "revenue_estimate":
            total_volume = query.with_entities(
                func.sum(TransactionAnalytics.amount)
            ).scalar()
            return float(total_volume * Decimal("0.029")) if total_volume else 0.0
        else:
            raise ValueError(f"Unknown transaction metric: {metric_def.name}")

    def _calculate_customer_metric(
        self,
        metric_def: MetricDefinition,
        start_date: datetime,
        end_date: datetime,
        filters: Dict[str, Any],
    ) -> float:
        """Calculate metrics based on customer data."""
        query = self.db.query(CustomerAnalytics)
        if "lifecycle_stage" in filters:
            query = query.filter(
                CustomerAnalytics.lifecycle_stage.in_(filters["lifecycle_stage"])
            )
        if "min_ltv" in filters:
            query = query.filter(CustomerAnalytics.predicted_ltv >= filters["min_ltv"])
        if "max_risk_score" in filters:
            query = query.filter(
                CustomerAnalytics.overall_risk_score <= filters["max_risk_score"]
            )
        if metric_def.name == "total_customer_count":
            return float(query.count())
        elif metric_def.name == "average_customer_ltv":
            result = query.with_entities(
                func.avg(CustomerAnalytics.predicted_ltv)
            ).scalar()
            return float(result) if result else 0.0
        elif metric_def.name == "high_value_customer_ratio":
            total_count = query.count()
            ltv_threshold = query.with_entities(
                func.percentile_cont(0.8).within_group(CustomerAnalytics.predicted_ltv)
            ).scalar()
            high_value_count = query.filter(
                CustomerAnalytics.predicted_ltv >= ltv_threshold
            ).count()
            return high_value_count / total_count if total_count > 0 else 0.0
        elif metric_def.name == "customer_churn_risk":
            result = query.with_entities(
                func.avg(CustomerAnalytics.churn_probability)
            ).scalar()
            return float(result) if result else 0.0
        elif metric_def.name == "active_customer_ratio":
            total_count = query.count()
            active_count = query.filter(
                CustomerAnalytics.lifecycle_stage == "active"
            ).count()
            return active_count / total_count if total_count > 0 else 0.0
        elif metric_def.name == "average_account_age":
            result = query.with_entities(
                func.avg(CustomerAnalytics.account_age_days)
            ).scalar()
            return float(result) if result else 0.0
        elif metric_def.name == "kyc_completion_rate":
            total_count = query.count()
            completed_count = query.filter(
                CustomerAnalytics.kyc_status == "completed"
            ).count()
            return completed_count / total_count if total_count > 0 else 0.0
        else:
            raise ValueError(f"Unknown customer metric: {metric_def.name}")

    def _calculate_performance_metric(
        self,
        metric_def: MetricDefinition,
        start_date: datetime,
        end_date: datetime,
        filters: Dict[str, Any],
    ) -> float:
        """Calculate metrics based on performance data."""
        query = self.db.query(PerformanceMetrics).filter(
            and_(
                PerformanceMetrics.measurement_timestamp >= start_date,
                PerformanceMetrics.measurement_timestamp <= end_date,
            )
        )
        if "service_name" in filters:
            query = query.filter(
                PerformanceMetrics.service_name.in_(filters["service_name"])
            )
        if metric_def.name == "average_response_time":
            result = query.with_entities(
                func.avg(PerformanceMetrics.response_time_ms)
            ).scalar()
            return float(result) if result else 0.0
        elif metric_def.name == "system_availability":
            result = query.with_entities(
                func.avg(PerformanceMetrics.transaction_success_rate)
            ).scalar()
            return float(result) if result else 0.0
        elif metric_def.name == "total_throughput":
            result = query.with_entities(
                func.sum(PerformanceMetrics.throughput_rps)
            ).scalar()
            return float(result) if result else 0.0
        elif metric_def.name == "average_error_rate":
            result = query.with_entities(
                func.avg(PerformanceMetrics.error_rate)
            ).scalar()
            return float(result) if result else 0.0
        elif metric_def.name == "peak_response_time":
            result = query.with_entities(
                func.max(PerformanceMetrics.response_time_ms)
            ).scalar()
            return float(result) if result else 0.0
        else:
            raise ValueError(f"Unknown performance metric: {metric_def.name}")

    def calculate_trend_analysis(
        self, metric_name: str, periods: int = 7, period_type: str = "daily"
    ) -> Dict[str, Any]:
        """
        Calculate trend analysis for a metric over multiple periods.

        Args:
            metric_name: Name of the metric to analyze
            periods: Number of periods to analyze
            period_type: Type of period ('daily', 'weekly', 'monthly')

        Returns:
            Dictionary containing trend analysis results
        """
        if period_type == "daily":
            period_delta = timedelta(days=1)
        elif period_type == "weekly":
            period_delta = timedelta(weeks=1)
        elif period_type == "monthly":
            period_delta = timedelta(days=30)
        else:
            raise ValueError(f"Unknown period type: {period_type}")
        end_date = datetime.now(timezone.utc)
        trend_data = []
        for i in range(periods):
            period_end = end_date - period_delta * i
            period_start = period_end - period_delta
            try:
                result = self.calculate_metric(metric_name, period_start, period_end)
                trend_data.append(
                    {
                        "period": i,
                        "start_date": period_start.isoformat(),
                        "end_date": period_end.isoformat(),
                        "value": result.value,
                    }
                )
            except Exception as e:
                self.logger.error(f"Error calculating trend for period {i}: {str(e)}")
        trend_data.reverse()
        values = [data["value"] for data in trend_data]
        if len(values) >= 2:
            x = np.arange(len(values))
            y = np.array(values)
            slope, intercept = np.polyfit(x, y, 1)
            correlation = np.corrcoef(x, y)[0, 1] if len(values) > 1 else 0
            if slope > 0:
                trend_direction = "increasing"
            elif slope < 0:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        else:
            slope = 0
            correlation = 0
            trend_direction = "insufficient_data"
        return {
            "metric_name": metric_name,
            "period_type": period_type,
            "periods_analyzed": len(trend_data),
            "trend_data": trend_data,
            "statistics": {
                "slope": slope,
                "correlation": correlation,
                "trend_direction": trend_direction,
                "min_value": min(values) if values else 0,
                "max_value": max(values) if values else 0,
                "average_value": np.mean(values) if values else 0,
                "standard_deviation": np.std(values) if values else 0,
            },
        }

    def calculate_comparative_analysis(
        self,
        metric_name: str,
        comparison_filters: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Calculate comparative analysis for a metric across different segments.

        Args:
            metric_name: Name of the metric to compare
            comparison_filters: List of filter sets for comparison
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            Dictionary containing comparative analysis results
        """
        comparison_results = []
        for i, filters in enumerate(comparison_filters):
            try:
                result = self.calculate_metric(
                    metric_name, start_date, end_date, filters
                )
                comparison_results.append(
                    {
                        "segment": f"Segment_{i + 1}",
                        "filters": filters,
                        "value": result.value,
                        "change_percentage": result.change_percentage,
                    }
                )
            except Exception as e:
                self.logger.error(
                    f"Error calculating comparative metric for segment {i}: {str(e)}"
                )
        values = [result["value"] for result in comparison_results]
        if values:
            best_segment = max(comparison_results, key=lambda x: x["value"])
            worst_segment = min(comparison_results, key=lambda x: x["value"])
            return {
                "metric_name": metric_name,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "segments": comparison_results,
                "summary": {
                    "best_performing_segment": best_segment,
                    "worst_performing_segment": worst_segment,
                    "average_value": np.mean(values),
                    "value_range": max(values) - min(values),
                    "coefficient_of_variation": (
                        np.std(values) / np.mean(values) if np.mean(values) != 0 else 0
                    ),
                },
            }
        else:
            return {
                "metric_name": metric_name,
                "error": "No valid segments for comparison",
            }

    def calculate_percentile_analysis(
        self,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        percentiles: List[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate percentile analysis for a metric.

        Args:
            metric_name: Name of the metric to analyze
            start_date: Start of the analysis period
            end_date: End of the analysis period
            percentiles: List of percentiles to calculate (default: [25, 50, 75, 90, 95, 99])

        Returns:
            Dictionary containing percentile analysis results
        """
        if percentiles is None:
            percentiles = [25, 50, 75, 90, 95, 99]
        if metric_name not in self._metric_definitions:
            raise ValueError(f"Unknown metric: {metric_name}")
        metric_def = self._metric_definitions[metric_name]
        if metric_def.data_source == "transactions":
            query = self.db.query(TransactionAnalytics).filter(
                and_(
                    TransactionAnalytics.transaction_date >= start_date,
                    TransactionAnalytics.transaction_date <= end_date,
                )
            )
            if metric_name == "transaction_amounts":
                values = [float(t.amount) for t in query.all()]
            elif metric_name == "risk_scores":
                values = [float(t.risk_score) for t in query.all() if t.risk_score]
            else:
                values = []
                for transaction in query.all():
                    pass
        elif metric_def.data_source == "customers":
            query = self.db.query(CustomerAnalytics)
            if metric_name == "customer_ltv":
                values = [
                    float(c.predicted_ltv) for c in query.all() if c.predicted_ltv
                ]
            elif metric_name == "customer_risk_scores":
                values = [
                    float(c.overall_risk_score)
                    for c in query.all()
                    if c.overall_risk_score
                ]
            else:
                values = []
        else:
            values = []
        if not values:
            return {
                "metric_name": metric_name,
                "error": "No data available for percentile analysis",
            }
        percentile_results = {}
        for p in percentiles:
            percentile_results[f"p{p}"] = float(np.percentile(values, p))
        return {
            "metric_name": metric_name,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "sample_size": len(values),
            "percentiles": percentile_results,
            "statistics": {
                "min": min(values),
                "max": max(values),
                "mean": np.mean(values),
                "median": np.median(values),
                "std_dev": np.std(values),
            },
        }

    def _load_default_metrics(self) -> Dict[str, MetricDefinition]:
        """Load default metric definitions."""
        metrics = {}
        metrics["total_transaction_count"] = MetricDefinition(
            name="total_transaction_count",
            type=MetricType.FINANCIAL,
            description="Total number of transactions",
            calculation_method="count",
            aggregation=AggregationType.COUNT,
            data_source="transactions",
        )
        metrics["total_transaction_volume"] = MetricDefinition(
            name="total_transaction_volume",
            type=MetricType.FINANCIAL,
            description="Total transaction volume",
            calculation_method="sum",
            aggregation=AggregationType.SUM,
            data_source="transactions",
        )
        metrics["average_transaction_amount"] = MetricDefinition(
            name="average_transaction_amount",
            type=MetricType.FINANCIAL,
            description="Average transaction amount",
            calculation_method="average",
            aggregation=AggregationType.AVERAGE,
            data_source="transactions",
        )
        metrics["revenue_estimate"] = MetricDefinition(
            name="revenue_estimate",
            type=MetricType.FINANCIAL,
            description="Estimated revenue from transaction fees",
            calculation_method="custom",
            aggregation=AggregationType.SUM,
            data_source="transactions",
        )
        metrics["high_risk_transaction_ratio"] = MetricDefinition(
            name="high_risk_transaction_ratio",
            type=MetricType.RISK,
            description="Ratio of high-risk transactions",
            calculation_method="ratio",
            aggregation=AggregationType.AVERAGE,
            data_source="transactions",
        )
        metrics["fraud_detection_rate"] = MetricDefinition(
            name="fraud_detection_rate",
            type=MetricType.RISK,
            description="Rate of fraud detection",
            calculation_method="ratio",
            aggregation=AggregationType.AVERAGE,
            data_source="transactions",
        )
        metrics["average_risk_score"] = MetricDefinition(
            name="average_risk_score",
            type=MetricType.RISK,
            description="Average risk score across transactions",
            calculation_method="average",
            aggregation=AggregationType.AVERAGE,
            data_source="transactions",
        )
        metrics["total_customer_count"] = MetricDefinition(
            name="total_customer_count",
            type=MetricType.CUSTOMER,
            description="Total number of customers",
            calculation_method="count",
            aggregation=AggregationType.COUNT,
            data_source="customers",
        )
        metrics["average_customer_ltv"] = MetricDefinition(
            name="average_customer_ltv",
            type=MetricType.CUSTOMER,
            description="Average customer lifetime value",
            calculation_method="average",
            aggregation=AggregationType.AVERAGE,
            data_source="customers",
        )
        metrics["customer_churn_risk"] = MetricDefinition(
            name="customer_churn_risk",
            type=MetricType.CUSTOMER,
            description="Average customer churn risk",
            calculation_method="average",
            aggregation=AggregationType.AVERAGE,
            data_source="customers",
        )
        metrics["average_response_time"] = MetricDefinition(
            name="average_response_time",
            type=MetricType.PERFORMANCE,
            description="Average system response time",
            calculation_method="average",
            aggregation=AggregationType.AVERAGE,
            data_source="performance",
        )
        metrics["system_availability"] = MetricDefinition(
            name="system_availability",
            type=MetricType.PERFORMANCE,
            description="System availability percentage",
            calculation_method="average",
            aggregation=AggregationType.AVERAGE,
            data_source="performance",
        )
        metrics["large_transaction_count"] = MetricDefinition(
            name="large_transaction_count",
            type=MetricType.COMPLIANCE,
            description="Number of large transactions requiring reporting",
            calculation_method="count",
            aggregation=AggregationType.COUNT,
            data_source="transactions",
            filters={"min_amount": 10000},
        )
        metrics["suspicious_activity_ratio"] = MetricDefinition(
            name="suspicious_activity_ratio",
            type=MetricType.COMPLIANCE,
            description="Ratio of suspicious activities",
            calculation_method="ratio",
            aggregation=AggregationType.AVERAGE,
            data_source="transactions",
        )
        return metrics

    def add_custom_metric(self, metric_definition: MetricDefinition) -> object:
        """Add a custom metric definition."""
        self._metric_definitions[metric_definition.name] = metric_definition
        self.logger.info(f"Added custom metric: {metric_definition.name}")

    def get_available_metrics(self) -> List[Dict[str, Any]]:
        """Get list of available metrics."""
        return [
            {
                "name": metric.name,
                "type": metric.type.value,
                "description": metric.description,
                "data_source": metric.data_source,
                "aggregation": metric.aggregation.value,
            }
            for metric in self._metric_definitions.values()
        ]

    def calculate_kpi_dashboard(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate a comprehensive KPI dashboard."""
        key_metrics = [
            "total_transaction_count",
            "total_transaction_volume",
            "average_transaction_amount",
            "revenue_estimate",
            "high_risk_transaction_ratio",
            "fraud_detection_rate",
            "total_customer_count",
            "average_customer_ltv",
            "average_response_time",
            "system_availability",
        ]
        results = self.calculate_multiple_metrics(key_metrics, start_date, end_date)
        kpi_data = {}
        for result in results:
            kpi_data[result.metric_name] = {
                "value": result.value,
                "previous_value": result.previous_value,
                "change_percentage": result.change_percentage,
                "trend": (
                    "up"
                    if result.change_percentage and result.change_percentage > 0
                    else "down"
                ),
            }
        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "kpis": kpi_data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
