import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .data_models import (
    AlertConfiguration,
    CustomerAnalytics,
    PerformanceMetrics,
    TransactionAnalytics,
)
from .reporting_engine import ReportingEngine


class WidgetType(Enum):
    """Types of dashboard widgets."""

    KPI_CARD = "kpi_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    TABLE = "table"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    ALERT_LIST = "alert_list"


class RefreshInterval(Enum):
    """Dashboard refresh intervals."""

    REAL_TIME = 5
    FAST = 30
    NORMAL = 300
    SLOW = 1800


@dataclass
class Widget:
    """Dashboard widget configuration."""

    id: str
    type: WidgetType
    title: str
    data_source: str
    refresh_interval: RefreshInterval
    config: Dict[str, Any]
    position: Dict[str, int]
    filters: Dict[str, Any] = None

    def __post_init__(self) -> object:
        if self.filters is None:
            self.filters = {}


@dataclass
class Dashboard:
    """Dashboard configuration."""

    id: str
    name: str
    description: str
    widgets: List[Widget]
    layout: str = "grid"
    theme: str = "light"
    auto_refresh: bool = True
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self) -> object:
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)


class DashboardService:
    """
    Advanced dashboard service for real-time financial analytics.

    Features:
    - Real-time data updates
    - Customizable widgets
    - Interactive charts
    - Alert management
    - Multi-user support
    - Export capabilities
    """

    def __init__(self, db_session: Session) -> None:
        self.db = db_session
        self.reporting_engine = ReportingEngine(db_session)
        self.logger = logging.getLogger(__name__)
        self._active_dashboards = {}
        self._widget_cache = {}

    async def create_dashboard(self, dashboard_config: Dict[str, Any]) -> Dashboard:
        """Create a new dashboard with specified configuration."""
        try:
            widgets = []
            for widget_config in dashboard_config.get("widgets", []):
                widget = Widget(
                    id=widget_config["id"],
                    type=WidgetType(widget_config["type"]),
                    title=widget_config["title"],
                    data_source=widget_config["data_source"],
                    refresh_interval=RefreshInterval(
                        widget_config.get(
                            "refresh_interval", RefreshInterval.NORMAL.value
                        )
                    ),
                    config=widget_config.get("config", {}),
                    position=widget_config["position"],
                    filters=widget_config.get("filters", {}),
                )
                widgets.append(widget)
            dashboard = Dashboard(
                id=dashboard_config["id"],
                name=dashboard_config["name"],
                description=dashboard_config.get("description", ""),
                widgets=widgets,
                layout=dashboard_config.get("layout", "grid"),
                theme=dashboard_config.get("theme", "light"),
                auto_refresh=dashboard_config.get("auto_refresh", True),
            )
            self._active_dashboards[dashboard.id] = dashboard
            self.logger.info(f"Created dashboard: {dashboard.name}")
            return dashboard
        except Exception as e:
            self.logger.error(f"Error creating dashboard: {str(e)}")
            raise

    async def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get complete dashboard data with all widget data."""
        if dashboard_id not in self._active_dashboards:
            raise ValueError(f"Dashboard {dashboard_id} not found")
        dashboard = self._active_dashboards[dashboard_id]
        widget_data = {}
        for widget in dashboard.widgets:
            try:
                data = await self._get_widget_data(widget)
                widget_data[widget.id] = data
            except Exception as e:
                self.logger.error(
                    f"Error getting data for widget {widget.id}: {str(e)}"
                )
                widget_data[widget.id] = {"error": str(e)}
        return {
            "dashboard": asdict(dashboard),
            "widget_data": widget_data,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def _get_widget_data(self, widget: Widget) -> Dict[str, Any]:
        """Get data for a specific widget."""
        cache_key = f"{widget.id}_{hash(str(widget.filters))}"
        if cache_key in self._widget_cache:
            cached_data, cache_time = self._widget_cache[cache_key]
            if datetime.now(timezone.utc) - cache_time < timedelta(
                seconds=widget.refresh_interval.value
            ):
                return cached_data
        if widget.data_source == "transaction_summary":
            data = await self._get_transaction_summary_data(widget)
        elif widget.data_source == "customer_metrics":
            data = await self._get_customer_metrics_data(widget)
        elif widget.data_source == "risk_metrics":
            data = await self._get_risk_metrics_data(widget)
        elif widget.data_source == "performance_metrics":
            data = await self._get_performance_metrics_data(widget)
        elif widget.data_source == "revenue_metrics":
            data = await self._get_revenue_metrics_data(widget)
        elif widget.data_source == "alerts":
            data = await self._get_alerts_data(widget)
        else:
            raise ValueError(f"Unknown data source: {widget.data_source}")
        self._widget_cache[cache_key] = (data, datetime.now(timezone.utc))
        return data

    async def _get_transaction_summary_data(self, widget: Widget) -> Dict[str, Any]:
        """Get transaction summary data for widgets."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=1)
        if "time_range" in widget.filters:
            time_range = widget.filters["time_range"]
            if time_range == "last_hour":
                start_date = end_date - timedelta(hours=1)
            elif time_range == "last_day":
                start_date = end_date - timedelta(days=1)
            elif time_range == "last_week":
                start_date = end_date - timedelta(weeks=1)
            elif time_range == "last_month":
                start_date = end_date - timedelta(days=30)
        query = self.db.query(TransactionAnalytics).filter(
            and_(
                TransactionAnalytics.transaction_date >= start_date,
                TransactionAnalytics.transaction_date <= end_date,
            )
        )
        if "currency" in widget.filters:
            query = query.filter(
                TransactionAnalytics.currency.in_(widget.filters["currency"])
            )
        if "transaction_type" in widget.filters:
            query = query.filter(
                TransactionAnalytics.transaction_type.in_(
                    widget.filters["transaction_type"]
                )
            )
        transactions = query.all()
        if widget.type == WidgetType.KPI_CARD:
            return self._format_kpi_data(transactions, widget.config)
        elif widget.type == WidgetType.LINE_CHART:
            return self._format_line_chart_data(transactions, widget.config)
        elif widget.type == WidgetType.BAR_CHART:
            return self._format_bar_chart_data(transactions, widget.config)
        elif widget.type == WidgetType.PIE_CHART:
            return self._format_pie_chart_data(transactions, widget.config)
        elif widget.type == WidgetType.TABLE:
            return self._format_table_data(transactions, widget.config)
        else:
            return {"error": f"Unsupported widget type: {widget.type}"}

    async def _get_customer_metrics_data(self, widget: Widget) -> Dict[str, Any]:
        """Get customer metrics data for widgets."""
        customers = self.db.query(CustomerAnalytics).all()
        if widget.type == WidgetType.KPI_CARD:
            if widget.config.get("metric") == "total_customers":
                return {
                    "value": len(customers),
                    "label": "Total Customers",
                    "trend": self._calculate_customer_trend(),
                }
            elif widget.config.get("metric") == "average_ltv":
                avg_ltv = (
                    sum((float(c.predicted_ltv) for c in customers if c.predicted_ltv))
                    / len(customers)
                    if customers
                    else 0
                )
                return {
                    "value": round(avg_ltv, 2),
                    "label": "Average LTV",
                    "format": "currency",
                }
        elif widget.type == WidgetType.PIE_CHART:
            if widget.config.get("metric") == "lifecycle_stages":
                stages = {}
                for customer in customers:
                    stage = customer.lifecycle_stage or "unknown"
                    stages[stage] = stages.get(stage, 0) + 1
                return {
                    "data": [{"name": k, "value": v} for k, v in stages.items()],
                    "title": "Customer Lifecycle Stages",
                }
        return {"error": "Unsupported customer metric configuration"}

    async def _get_risk_metrics_data(self, widget: Widget) -> Dict[str, Any]:
        """Get risk metrics data for widgets."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=1)
        high_risk_count = (
            self.db.query(func.count(TransactionAnalytics.id))
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= start_date,
                    TransactionAnalytics.transaction_date <= end_date,
                    TransactionAnalytics.risk_score > 0.7,
                )
            )
            .scalar()
        )
        total_count = (
            self.db.query(func.count(TransactionAnalytics.id))
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= start_date,
                    TransactionAnalytics.transaction_date <= end_date,
                )
            )
            .scalar()
        )
        if widget.type == WidgetType.KPI_CARD:
            if widget.config.get("metric") == "high_risk_transactions":
                return {
                    "value": high_risk_count,
                    "label": "High Risk Transactions",
                    "trend": "stable",
                }
            elif widget.config.get("metric") == "risk_ratio":
                ratio = high_risk_count / total_count * 100 if total_count > 0 else 0
                return {
                    "value": round(ratio, 2),
                    "label": "Risk Ratio (%)",
                    "format": "percentage",
                }
        elif widget.type == WidgetType.GAUGE:
            if widget.config.get("metric") == "overall_risk_score":
                avg_risk = (
                    self.db.query(func.avg(TransactionAnalytics.risk_score))
                    .filter(
                        and_(
                            TransactionAnalytics.transaction_date >= start_date,
                            TransactionAnalytics.transaction_date <= end_date,
                        )
                    )
                    .scalar()
                )
                return {
                    "value": float(avg_risk) if avg_risk else 0,
                    "min": 0,
                    "max": 1,
                    "title": "Overall Risk Score",
                    "thresholds": [
                        {"value": 0.3, "color": "green"},
                        {"value": 0.7, "color": "yellow"},
                        {"value": 1.0, "color": "red"},
                    ],
                }
        return {"error": "Unsupported risk metric configuration"}

    async def _get_performance_metrics_data(self, widget: Widget) -> Dict[str, Any]:
        """Get performance metrics data for widgets."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=1)
        performance_data = (
            self.db.query(PerformanceMetrics)
            .filter(
                and_(
                    PerformanceMetrics.measurement_timestamp >= start_date,
                    PerformanceMetrics.measurement_timestamp <= end_date,
                )
            )
            .all()
        )
        if widget.type == WidgetType.KPI_CARD:
            if widget.config.get("metric") == "avg_response_time":
                avg_response = (
                    sum((p.response_time_ms for p in performance_data))
                    / len(performance_data)
                    if performance_data
                    else 0
                )
                return {
                    "value": round(avg_response, 0),
                    "label": "Avg Response Time (ms)",
                    "trend": "stable",
                }
            elif widget.config.get("metric") == "system_availability":
                avg_success = (
                    sum(
                        (
                            float(p.transaction_success_rate)
                            for p in performance_data
                            if p.transaction_success_rate
                        )
                    )
                    / len(performance_data)
                    if performance_data
                    else 0
                )
                return {
                    "value": round(avg_success * 100, 2),
                    "label": "System Availability (%)",
                    "format": "percentage",
                }
        elif widget.type == WidgetType.LINE_CHART:
            if widget.config.get("metric") == "response_time_trend":
                data_points = []
                for p in performance_data:
                    data_points.append(
                        {
                            "timestamp": p.measurement_timestamp.isoformat(),
                            "value": p.response_time_ms,
                        }
                    )
                return {
                    "data": data_points,
                    "title": "Response Time Trend",
                    "yAxis": "Response Time (ms)",
                }
        return {"error": "Unsupported performance metric configuration"}

    async def _get_revenue_metrics_data(self, widget: Widget) -> Dict[str, Any]:
        """Get revenue metrics data for widgets."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)
        transactions = (
            self.db.query(TransactionAnalytics)
            .filter(
                and_(
                    TransactionAnalytics.transaction_date >= start_date,
                    TransactionAnalytics.transaction_date <= end_date,
                )
            )
            .all()
        )
        total_volume = sum((float(t.amount) for t in transactions))
        estimated_revenue = total_volume * 0.029
        if widget.type == WidgetType.KPI_CARD:
            if widget.config.get("metric") == "total_revenue":
                return {
                    "value": round(estimated_revenue, 2),
                    "label": "Total Revenue (30d)",
                    "format": "currency",
                    "trend": "increasing",
                }
            elif widget.config.get("metric") == "transaction_volume":
                return {
                    "value": round(total_volume, 2),
                    "label": "Transaction Volume (30d)",
                    "format": "currency",
                }
        elif widget.type == WidgetType.LINE_CHART:
            if widget.config.get("metric") == "daily_revenue":
                daily_revenue = {}
                for transaction in transactions:
                    date_key = transaction.transaction_date.date()
                    if date_key not in daily_revenue:
                        daily_revenue[date_key] = 0
                    daily_revenue[date_key] += float(transaction.amount) * 0.029
                data_points = []
                for date, revenue in sorted(daily_revenue.items()):
                    data_points.append(
                        {"date": date.isoformat(), "value": round(revenue, 2)}
                    )
                return {
                    "data": data_points,
                    "title": "Daily Revenue Trend",
                    "yAxis": "Revenue ($)",
                }
        return {"error": "Unsupported revenue metric configuration"}

    async def _get_alerts_data(self, widget: Widget) -> Dict[str, Any]:
        """Get alerts data for widgets."""
        active_alerts = (
            self.db.query(AlertConfiguration).filter(AlertConfiguration.is_active).all()
        )
        recent_alerts = [
            alert
            for alert in active_alerts
            if alert.last_triggered
            and alert.last_triggered > datetime.now(timezone.utc) - timedelta(hours=24)
        ]
        if widget.type == WidgetType.ALERT_LIST:
            alerts_data = []
            for alert in recent_alerts:
                alerts_data.append(
                    {
                        "id": str(alert.id),
                        "name": alert.alert_name,
                        "severity": alert.severity_level,
                        "last_triggered": (
                            alert.last_triggered.isoformat()
                            if alert.last_triggered
                            else None
                        ),
                        "trigger_count": alert.trigger_count,
                    }
                )
            return {
                "alerts": alerts_data,
                "total_active": len(active_alerts),
                "recent_triggers": len(recent_alerts),
            }
        elif widget.type == WidgetType.KPI_CARD:
            if widget.config.get("metric") == "active_alerts":
                return {
                    "value": len(recent_alerts),
                    "label": "Active Alerts (24h)",
                    "trend": "stable",
                }
        return {"error": "Unsupported alerts configuration"}

    def _format_kpi_data(
        self, transactions: List, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format data for KPI card widgets."""
        metric = config.get("metric", "total_transactions")
        if metric == "total_transactions":
            return {
                "value": len(transactions),
                "label": "Total Transactions",
                "trend": "stable",
            }
        elif metric == "total_volume":
            total = sum((float(t.amount) for t in transactions))
            return {
                "value": round(total, 2),
                "label": "Total Volume",
                "format": "currency",
            }
        elif metric == "average_transaction":
            avg = (
                sum((float(t.amount) for t in transactions)) / len(transactions)
                if transactions
                else 0
            )
            return {
                "value": round(avg, 2),
                "label": "Average Transaction",
                "format": "currency",
            }
        return {"error": f"Unknown KPI metric: {metric}"}

    def _format_line_chart_data(
        self, transactions: List, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format data for line chart widgets."""
        time_series = {}
        for transaction in transactions:
            time_key = transaction.transaction_date.replace(
                minute=0, second=0, microsecond=0
            )
            if time_key not in time_series:
                time_series[time_key] = {"count": 0, "volume": 0}
            time_series[time_key]["count"] += 1
            time_series[time_key]["volume"] += float(transaction.amount)
        data_points = []
        for timestamp, data in sorted(time_series.items()):
            data_points.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "count": data["count"],
                    "volume": round(data["volume"], 2),
                }
            )
        return {
            "data": data_points,
            "title": config.get("title", "Transaction Trends"),
            "xAxis": "Time",
            "yAxis": config.get("y_axis", "Count"),
        }

    def _format_bar_chart_data(
        self, transactions: List, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format data for bar chart widgets."""
        group_by = config.get("group_by", "transaction_type")
        groups = {}
        for transaction in transactions:
            if group_by == "transaction_type":
                key = transaction.transaction_type
            elif group_by == "currency":
                key = transaction.currency
            elif group_by == "country":
                key = transaction.country_code or "Unknown"
            elif group_by == "payment_method":
                key = transaction.payment_method or "Unknown"
            else:
                key = "Other"
            if key not in groups:
                groups[key] = {"count": 0, "volume": 0}
            groups[key]["count"] += 1
            groups[key]["volume"] += float(transaction.amount)
        data_points = []
        for category, data in groups.items():
            data_points.append(
                {
                    "category": category,
                    "count": data["count"],
                    "volume": round(data["volume"], 2),
                }
            )
        return {
            "data": data_points,
            "title": config.get("title", f"Transactions by {group_by}"),
            "xAxis": group_by.replace("_", " ").title(),
            "yAxis": config.get("y_axis", "Count"),
        }

    def _format_pie_chart_data(
        self, transactions: List, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format data for pie chart widgets."""
        group_by = config.get("group_by", "transaction_type")
        groups = {}
        for transaction in transactions:
            if group_by == "transaction_type":
                key = transaction.transaction_type
            elif group_by == "currency":
                key = transaction.currency
            elif group_by == "country":
                key = transaction.country_code or "Unknown"
            else:
                key = "Other"
            groups[key] = groups.get(key, 0) + float(transaction.amount)
        data_points = []
        for category, value in groups.items():
            data_points.append({"name": category, "value": round(value, 2)})
        return {
            "data": data_points,
            "title": config.get("title", f"Distribution by {group_by}"),
        }

    def _format_table_data(
        self, transactions: List, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format data for table widgets."""
        max_rows = config.get("max_rows", 100)
        limited_transactions = transactions[:max_rows]
        columns = config.get(
            "columns",
            [
                "transaction_id",
                "amount",
                "currency",
                "transaction_type",
                "transaction_date",
            ],
        )
        rows = []
        for transaction in limited_transactions:
            row = {}
            for column in columns:
                if hasattr(transaction, column):
                    value = getattr(transaction, column)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    elif hasattr(value, "__str__"):
                        value = str(value)
                    row[column] = value
            rows.append(row)
        return {
            "columns": columns,
            "rows": rows,
            "total_rows": len(transactions),
            "displayed_rows": len(rows),
        }

    def _calculate_customer_trend(self) -> str:
        """Calculate customer growth trend."""
        return "increasing"

    async def update_widget(
        self, dashboard_id: str, widget_id: str, config: Dict[str, Any]
    ) -> bool:
        """Update widget configuration."""
        if dashboard_id not in self._active_dashboards:
            return False
        dashboard = self._active_dashboards[dashboard_id]
        for widget in dashboard.widgets:
            if widget.id == widget_id:
                for key, value in config.items():
                    if hasattr(widget, key):
                        setattr(widget, key, value)
                cache_keys_to_remove = [
                    key
                    for key in self._widget_cache.keys()
                    if key.startswith(widget_id)
                ]
                for key in cache_keys_to_remove:
                    del self._widget_cache[key]
                dashboard.updated_at = datetime.now(timezone.utc)
                return True
        return False

    async def export_dashboard(
        self, dashboard_id: str, format: str = "json"
    ) -> Dict[str, Any]:
        """Export dashboard configuration and data."""
        if dashboard_id not in self._active_dashboards:
            raise ValueError(f"Dashboard {dashboard_id} not found")
        dashboard_data = await self.get_dashboard_data(dashboard_id)
        if format == "json":
            return dashboard_data
        elif format == "csv":
            csv_data = {}
            for widget_id, data in dashboard_data["widget_data"].items():
                if "rows" in data:
                    csv_data[widget_id] = data["rows"]
            return csv_data
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def get_predefined_dashboards(self) -> List[Dict[str, Any]]:
        """Get predefined dashboard templates."""
        return [
            {
                "id": "executive_summary",
                "name": "Executive Summary",
                "description": "High-level business metrics and KPIs",
                "widgets": [
                    {
                        "id": "total_revenue",
                        "type": "kpi_card",
                        "title": "Total Revenue",
                        "data_source": "revenue_metrics",
                        "refresh_interval": 300,
                        "config": {"metric": "total_revenue"},
                        "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                    },
                    {
                        "id": "total_transactions",
                        "type": "kpi_card",
                        "title": "Total Transactions",
                        "data_source": "transaction_summary",
                        "refresh_interval": 300,
                        "config": {"metric": "total_transactions"},
                        "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                    },
                    {
                        "id": "active_customers",
                        "type": "kpi_card",
                        "title": "Active Customers",
                        "data_source": "customer_metrics",
                        "refresh_interval": 300,
                        "config": {"metric": "total_customers"},
                        "position": {"x": 6, "y": 0, "width": 3, "height": 2},
                    },
                    {
                        "id": "system_health",
                        "type": "gauge",
                        "title": "System Health",
                        "data_source": "performance_metrics",
                        "refresh_interval": 30,
                        "config": {"metric": "overall_risk_score"},
                        "position": {"x": 9, "y": 0, "width": 3, "height": 2},
                    },
                ],
            },
            {
                "id": "risk_monitoring",
                "name": "Risk Monitoring",
                "description": "Real-time risk assessment and fraud detection",
                "widgets": [
                    {
                        "id": "risk_score_gauge",
                        "type": "gauge",
                        "title": "Overall Risk Score",
                        "data_source": "risk_metrics",
                        "refresh_interval": 30,
                        "config": {"metric": "overall_risk_score"},
                        "position": {"x": 0, "y": 0, "width": 4, "height": 3},
                    },
                    {
                        "id": "high_risk_transactions",
                        "type": "kpi_card",
                        "title": "High Risk Transactions",
                        "data_source": "risk_metrics",
                        "refresh_interval": 30,
                        "config": {"metric": "high_risk_transactions"},
                        "position": {"x": 4, "y": 0, "width": 4, "height": 3},
                    },
                    {
                        "id": "active_alerts",
                        "type": "alert_list",
                        "title": "Active Alerts",
                        "data_source": "alerts",
                        "refresh_interval": 30,
                        "config": {},
                        "position": {"x": 8, "y": 0, "width": 4, "height": 3},
                    },
                ],
            },
            {
                "id": "operational_dashboard",
                "name": "Operational Dashboard",
                "description": "System performance and operational metrics",
                "widgets": [
                    {
                        "id": "response_time_trend",
                        "type": "line_chart",
                        "title": "Response Time Trend",
                        "data_source": "performance_metrics",
                        "refresh_interval": 30,
                        "config": {"metric": "response_time_trend"},
                        "position": {"x": 0, "y": 0, "width": 6, "height": 4},
                    },
                    {
                        "id": "system_availability",
                        "type": "kpi_card",
                        "title": "System Availability",
                        "data_source": "performance_metrics",
                        "refresh_interval": 30,
                        "config": {"metric": "system_availability"},
                        "position": {"x": 6, "y": 0, "width": 3, "height": 2},
                    },
                    {
                        "id": "avg_response_time",
                        "type": "kpi_card",
                        "title": "Avg Response Time",
                        "data_source": "performance_metrics",
                        "refresh_interval": 30,
                        "config": {"metric": "avg_response_time"},
                        "position": {"x": 9, "y": 0, "width": 3, "height": 2},
                    },
                ],
            },
        ]
