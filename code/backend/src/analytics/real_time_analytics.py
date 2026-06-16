import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

"\nReal-Time Analytics\n==================\n\nReal-time analytics engine for financial data processing and monitoring.\nProvides streaming analytics, real-time alerts, and live dashboards.\n"


class StreamEventType(Enum):
    """Types of streaming events."""

    TRANSACTION = "transaction"
    USER_ACTION = "user_action"
    SYSTEM_METRIC = "system_metric"
    ALERT = "alert"
    FRAUD_DETECTION = "fraud_detection"


class AlertSeverity(Enum):
    """Alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class StreamEvent:
    """Streaming event data structure."""

    event_id: str
    event_type: StreamEventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "source": self.source,
            "user_id": self.user_id,
            "session_id": self.session_id,
        }


@dataclass
class RealTimeAlert:
    """Real-time alert data structure."""

    alert_id: str
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    data: Dict[str, Any]
    acknowledged: bool = False
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
        }


@dataclass
class MetricWindow:
    """Time window for metric calculations."""

    window_size: timedelta
    slide_interval: timedelta
    metric_name: str
    aggregation_function: str

    def __post_init__(self) -> object:
        self.data_points = deque()
        self.current_value = 0.0
        self.last_calculation = datetime.now(timezone.utc)


class RealTimeAnalytics:
    """
    Real-time analytics engine for financial data processing.

    Features:
    - Streaming event processing
    - Real-time metric calculation
    - Sliding window analytics
    - Anomaly detection
    - Real-time alerting
    - Live dashboard updates
    """

    def __init__(self, db_session: Session) -> None:
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self._event_queue = asyncio.Queue()
        self._event_processors = {}
        self._is_processing = False
        self._metric_windows = {}
        self._real_time_metrics = {}
        self._metric_history = defaultdict(deque)
        self._alert_rules = {}
        self._active_alerts = {}
        self._alert_callbacks = []
        self._dashboard_subscribers = set()
        self._metric_subscribers = defaultdict(set)
        self._initialize_default_windows()
        self._initialize_default_alert_rules()

    def _initialize_default_windows(self) -> object:
        """Initialize default metric windows."""
        self._metric_windows["transaction_volume_1m"] = MetricWindow(
            window_size=timedelta(minutes=1),
            slide_interval=timedelta(seconds=10),
            metric_name="transaction_volume",
            aggregation_function="sum",
        )
        self._metric_windows["transaction_count_1m"] = MetricWindow(
            window_size=timedelta(minutes=1),
            slide_interval=timedelta(seconds=10),
            metric_name="transaction_count",
            aggregation_function="count",
        )
        self._metric_windows["avg_transaction_amount_5m"] = MetricWindow(
            window_size=timedelta(minutes=5),
            slide_interval=timedelta(seconds=30),
            metric_name="avg_transaction_amount",
            aggregation_function="avg",
        )
        self._metric_windows["high_risk_ratio_5m"] = MetricWindow(
            window_size=timedelta(minutes=5),
            slide_interval=timedelta(seconds=30),
            metric_name="high_risk_ratio",
            aggregation_function="avg",
        )
        self._metric_windows["response_time_1m"] = MetricWindow(
            window_size=timedelta(minutes=1),
            slide_interval=timedelta(seconds=5),
            metric_name="response_time",
            aggregation_function="avg",
        )
        self._metric_windows["error_rate_5m"] = MetricWindow(
            window_size=timedelta(minutes=5),
            slide_interval=timedelta(seconds=30),
            metric_name="error_rate",
            aggregation_function="avg",
        )

    def _initialize_default_alert_rules(self) -> object:
        """Initialize default alert rules."""
        self._alert_rules = {
            "high_transaction_volume": {
                "metric": "transaction_volume_1m",
                "condition": "greater_than",
                "threshold": 1000000,
                "severity": AlertSeverity.HIGH,
                "cooldown": timedelta(minutes=5),
            },
            "high_risk_transaction_spike": {
                "metric": "high_risk_ratio_5m",
                "condition": "greater_than",
                "threshold": 0.1,
                "severity": AlertSeverity.CRITICAL,
                "cooldown": timedelta(minutes=10),
            },
            "system_performance_degradation": {
                "metric": "response_time_1m",
                "condition": "greater_than",
                "threshold": 2000,
                "severity": AlertSeverity.MEDIUM,
                "cooldown": timedelta(minutes=3),
            },
            "high_error_rate": {
                "metric": "error_rate_5m",
                "condition": "greater_than",
                "threshold": 0.05,
                "severity": AlertSeverity.HIGH,
                "cooldown": timedelta(minutes=5),
            },
            "fraud_detection_spike": {
                "metric": "fraud_detection_rate_5m",
                "condition": "greater_than",
                "threshold": 0.02,
                "severity": AlertSeverity.CRITICAL,
                "cooldown": timedelta(minutes=15),
            },
        }

    async def start_processing(self):
        """Start the real-time analytics processing."""
        if self._is_processing:
            return
        self._is_processing = True
        self.logger.info("Starting real-time analytics processing")
        asyncio.create_task(self._process_events())
        asyncio.create_task(self._calculate_metrics())
        asyncio.create_task(self._monitor_alerts())

    async def stop_processing(self):
        """Stop the real-time analytics processing."""
        self._is_processing = False
        self.logger.info("Stopping real-time analytics processing")

    async def ingest_event(self, event: StreamEvent):
        """Ingest a streaming event for processing."""
        await self._event_queue.put(event)

    async def _process_events(self):
        """Process streaming events from the queue."""
        while self._is_processing:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing event: {str(e)}")

    async def _handle_event(self, event: StreamEvent):
        """Handle a specific streaming event."""
        try:
            if event.event_type == StreamEventType.TRANSACTION:
                await self._process_transaction_event(event)
            elif event.event_type == StreamEventType.SYSTEM_METRIC:
                await self._process_system_metric_event(event)
            elif event.event_type == StreamEventType.FRAUD_DETECTION:
                await self._process_fraud_detection_event(event)
            elif event.event_type == StreamEventType.USER_ACTION:
                await self._process_user_action_event(event)
            await self._notify_subscribers(event)
        except Exception as e:
            self.logger.error(f"Error handling event {event.event_id}: {str(e)}")

    async def _process_transaction_event(self, event: StreamEvent):
        """Process transaction events."""
        transaction_data = event.data
        amount = transaction_data.get("amount", 0)
        risk_score = transaction_data.get("risk_score", 0)
        if "transaction_volume_1m" in self._metric_windows:
            window = self._metric_windows["transaction_volume_1m"]
            window.data_points.append((event.timestamp, amount))
        if "transaction_count_1m" in self._metric_windows:
            window = self._metric_windows["transaction_count_1m"]
            window.data_points.append((event.timestamp, 1))
        if "avg_transaction_amount_5m" in self._metric_windows:
            window = self._metric_windows["avg_transaction_amount_5m"]
            window.data_points.append((event.timestamp, amount))
        if "high_risk_ratio_5m" in self._metric_windows:
            window = self._metric_windows["high_risk_ratio_5m"]
            is_high_risk = 1 if risk_score > 0.7 else 0
            window.data_points.append((event.timestamp, is_high_risk))
        await self._check_transaction_alerts(transaction_data)

    async def _process_system_metric_event(self, event: StreamEvent):
        """Process system metric events."""
        metric_data = event.data
        metric_name = metric_data.get("metric_name")
        value = metric_data.get("value", 0)
        if (
            metric_name == "response_time"
            and "response_time_1m" in self._metric_windows
        ):
            window = self._metric_windows["response_time_1m"]
            window.data_points.append((event.timestamp, value))
        elif metric_name == "error_rate" and "error_rate_5m" in self._metric_windows:
            window = self._metric_windows["error_rate_5m"]
            window.data_points.append((event.timestamp, value))

    async def _process_fraud_detection_event(self, event: StreamEvent):
        """Process fraud detection events."""
        fraud_data = event.data
        is_fraud = fraud_data.get("is_fraud", False)
        if "fraud_detection_rate_5m" not in self._metric_windows:
            self._metric_windows["fraud_detection_rate_5m"] = MetricWindow(
                window_size=timedelta(minutes=5),
                slide_interval=timedelta(seconds=30),
                metric_name="fraud_detection_rate",
                aggregation_function="avg",
            )
        window = self._metric_windows["fraud_detection_rate_5m"]
        fraud_value = 1 if is_fraud else 0
        window.data_points.append((event.timestamp, fraud_value))
        if is_fraud:
            await self._create_alert(
                alert_type="fraud_detected",
                severity=AlertSeverity.CRITICAL,
                title="Fraud Detected",
                message=f"Fraudulent transaction detected: {fraud_data.get('transaction_id')}",
                data=fraud_data,
            )

    async def _process_user_action_event(self, event: StreamEvent):
        """Process user action events."""
        user_data = event.data
        user_data.get("action_type")

    async def _calculate_metrics(self):
        """Calculate real-time metrics from sliding windows."""
        while self._is_processing:
            try:
                current_time = datetime.now(timezone.utc)
                for window_name, window in self._metric_windows.items():
                    if current_time - window.last_calculation >= window.slide_interval:
                        await self._calculate_window_metric(
                            window_name, window, current_time
                        )
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error calculating metrics: {str(e)}")
                await asyncio.sleep(5)

    async def _calculate_window_metric(
        self, window_name: str, window: MetricWindow, current_time: datetime
    ):
        """Calculate metric for a specific window."""
        cutoff_time = current_time - window.window_size
        while window.data_points and window.data_points[0][0] < cutoff_time:
            window.data_points.popleft()
        if not window.data_points:
            window.current_value = 0.0
        else:
            values = [point[1] for point in window.data_points]
            if window.aggregation_function == "sum":
                window.current_value = sum(values)
            elif window.aggregation_function == "avg":
                window.current_value = sum(values) / len(values)
            elif window.aggregation_function == "count":
                window.current_value = len(values)
            elif window.aggregation_function == "min":
                window.current_value = min(values)
            elif window.aggregation_function == "max":
                window.current_value = max(values)
        self._real_time_metrics[window_name] = {
            "value": window.current_value,
            "timestamp": current_time.isoformat(),
            "data_points": len(window.data_points),
        }
        history = self._metric_history[window_name]
        history.append((current_time, window.current_value))
        if len(history) > 100:
            history.popleft()
        window.last_calculation = current_time
        await self._notify_metric_subscribers(window_name, window.current_value)

    async def _monitor_alerts(self):
        """Monitor metrics and trigger alerts."""
        while self._is_processing:
            try:
                current_time = datetime.now(timezone.utc)
                for rule_name, rule in self._alert_rules.items():
                    await self._check_alert_rule(rule_name, rule, current_time)
                await self._cleanup_resolved_alerts(current_time)
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Error monitoring alerts: {str(e)}")
                await asyncio.sleep(10)

    async def _check_alert_rule(
        self, rule_name: str, rule: Dict[str, Any], current_time: datetime
    ):
        """Check a specific alert rule."""
        metric_name = rule["metric"]
        if metric_name not in self._real_time_metrics:
            return
        metric_value = self._real_time_metrics[metric_name]["value"]
        threshold = rule["threshold"]
        condition = rule["condition"]
        alert_triggered = False
        if condition == "greater_than" and metric_value > threshold:
            alert_triggered = True
        elif condition == "less_than" and metric_value < threshold:
            alert_triggered = True
        elif condition == "equals" and metric_value == threshold:
            alert_triggered = True
        if alert_triggered and rule_name in self._active_alerts:
            last_alert_time = self._active_alerts[rule_name]["timestamp"]
            if current_time - last_alert_time < rule["cooldown"]:
                return
        if alert_triggered:
            await self._create_alert(
                alert_type=rule_name,
                severity=rule["severity"],
                title=f"Alert: {rule_name.replace('_', ' ').title()}",
                message=f"Metric {metric_name} value {metric_value} {condition} threshold {threshold}",
                data={
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "threshold": threshold,
                    "condition": condition,
                },
            )

    async def _create_alert(
        self,
        alert_type: str,
        severity: AlertSeverity,
        title: str,
        message: str,
        data: Dict[str, Any],
    ):
        """Create a new alert."""
        alert_id = f"{alert_type}_{int(datetime.now(timezone.utc).timestamp())}"
        alert = RealTimeAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(timezone.utc),
            data=data,
        )
        self._active_alerts[alert_type] = {"alert": alert, "timestamp": alert.timestamp}
        for callback in self._alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {str(e)}")
        self.logger.warning(f"Alert created: {title} - {message}")

    async def _cleanup_resolved_alerts(self, current_time: datetime):
        """Clean up resolved alerts."""
        cutoff_time = current_time - timedelta(hours=1)
        alerts_to_remove = []
        for alert_type, alert_info in self._active_alerts.items():
            if alert_info["timestamp"] < cutoff_time:
                alerts_to_remove.append(alert_type)
        for alert_type in alerts_to_remove:
            del self._active_alerts[alert_type]

    async def _check_transaction_alerts(self, transaction_data: Dict[str, Any]):
        """Check for immediate transaction-based alerts."""
        amount = transaction_data.get("amount", 0)
        risk_score = transaction_data.get("risk_score", 0)
        if amount > 50000:
            await self._create_alert(
                alert_type="large_transaction",
                severity=AlertSeverity.HIGH,
                title="Large Transaction Detected",
                message=f"Transaction of ${amount:,.2f} detected",
                data=transaction_data,
            )
        if risk_score > 0.9:
            await self._create_alert(
                alert_type="high_risk_transaction",
                severity=AlertSeverity.CRITICAL,
                title="High Risk Transaction",
                message=f"Transaction with risk score {risk_score:.2f} detected",
                data=transaction_data,
            )

    async def _notify_subscribers(self, event: StreamEvent):
        """Notify dashboard subscribers of new events."""
        if self._dashboard_subscribers:
            self.logger.debug(
                f"Notifying {len(self._dashboard_subscribers)} subscribers of event {event.event_id}"
            )

    async def _notify_metric_subscribers(self, metric_name: str, value: float):
        """Notify metric subscribers of updated values."""
        subscribers = self._metric_subscribers.get(metric_name, set())
        if subscribers:
            self.logger.debug(
                f"Notifying {len(subscribers)} subscribers of metric {metric_name}: {value}"
            )

    def subscribe_to_dashboard_updates(self, subscriber_id: str) -> object:
        """Subscribe to real-time dashboard updates."""
        self._dashboard_subscribers.add(subscriber_id)
        self.logger.info(f"Subscriber {subscriber_id} added to dashboard updates")

    def unsubscribe_from_dashboard_updates(self, subscriber_id: str) -> object:
        """Unsubscribe from real-time dashboard updates."""
        self._dashboard_subscribers.discard(subscriber_id)
        self.logger.info(f"Subscriber {subscriber_id} removed from dashboard updates")

    def subscribe_to_metric(self, metric_name: str, subscriber_id: str) -> object:
        """Subscribe to specific metric updates."""
        self._metric_subscribers[metric_name].add(subscriber_id)
        self.logger.info(f"Subscriber {subscriber_id} added to metric {metric_name}")

    def unsubscribe_from_metric(self, metric_name: str, subscriber_id: str) -> object:
        """Unsubscribe from specific metric updates."""
        self._metric_subscribers[metric_name].discard(subscriber_id)
        self.logger.info(
            f"Subscriber {subscriber_id} removed from metric {metric_name}"
        )

    def add_alert_callback(self, callback: Callable) -> object:
        """Add a callback function for alert notifications."""
        self._alert_callbacks.append(callback)

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics."""
        return self._real_time_metrics.copy()

    def get_metric_history(
        self, metric_name: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric."""
        if metric_name not in self._metric_history:
            return []
        history = list(self._metric_history[metric_name])[-limit:]
        return [
            {"timestamp": timestamp.isoformat(), "value": value}
            for timestamp, value in history
        ]

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        return [
            alert_info["alert"].to_dict() for alert_info in self._active_alerts.values()
        ]

    def acknowledge_alert(self, alert_type: str) -> bool:
        """Acknowledge an active alert."""
        if alert_type in self._active_alerts:
            self._active_alerts[alert_type]["alert"].acknowledged = True
            return True
        return False

    def resolve_alert(self, alert_type: str) -> bool:
        """Resolve an active alert."""
        if alert_type in self._active_alerts:
            self._active_alerts[alert_type]["alert"].resolved = True
            return True
        return False

    def add_custom_metric_window(
        self, window_name: str, window_config: Dict[str, Any]
    ) -> object:
        """Add a custom metric window."""
        window = MetricWindow(
            window_size=timedelta(seconds=window_config["window_size_seconds"]),
            slide_interval=timedelta(seconds=window_config["slide_interval_seconds"]),
            metric_name=window_config["metric_name"],
            aggregation_function=window_config["aggregation_function"],
        )
        self._metric_windows[window_name] = window
        self.logger.info(f"Added custom metric window: {window_name}")

    def add_custom_alert_rule(
        self, rule_name: str, rule_config: Dict[str, Any]
    ) -> object:
        """Add a custom alert rule."""
        self._alert_rules[rule_name] = {
            "metric": rule_config["metric"],
            "condition": rule_config["condition"],
            "threshold": rule_config["threshold"],
            "severity": AlertSeverity(rule_config["severity"]),
            "cooldown": timedelta(seconds=rule_config["cooldown_seconds"]),
        }
        self.logger.info(f"Added custom alert rule: {rule_name}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get real-time analytics system status."""
        return {
            "is_processing": self._is_processing,
            "event_queue_size": self._event_queue.qsize(),
            "active_windows": len(self._metric_windows),
            "active_alerts": len(self._active_alerts),
            "dashboard_subscribers": len(self._dashboard_subscribers),
            "metric_subscribers": sum(
                (len(subs) for subs in self._metric_subscribers.values())
            ),
            "last_update": datetime.now(timezone.utc).isoformat(),
        }

    async def simulate_transaction_event(self, transaction_data: Dict[str, Any]):
        """Simulate a transaction event for testing."""
        event = StreamEvent(
            event_id=f"sim_{int(datetime.now(timezone.utc).timestamp())}",
            event_type=StreamEventType.TRANSACTION,
            timestamp=datetime.now(timezone.utc),
            data=transaction_data,
            source="simulation",
            user_id=transaction_data.get("user_id"),
        )
        await self.ingest_event(event)

    async def simulate_system_metric_event(self, metric_name: str, value: float):
        """Simulate a system metric event for testing."""
        event = StreamEvent(
            event_id=f"sim_metric_{int(datetime.now(timezone.utc).timestamp())}",
            event_type=StreamEventType.SYSTEM_METRIC,
            timestamp=datetime.now(timezone.utc),
            data={"metric_name": metric_name, "value": value},
            source="simulation",
        )
        await self.ingest_event(event)
