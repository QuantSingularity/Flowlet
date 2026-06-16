import asyncio
import json
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

"\nSecurity Monitoring Service\n===========================\n\nComprehensive security monitoring and incident response system.\nProvides real-time security event monitoring, alerting, and forensic capabilities.\n"


class EventSeverity(Enum):
    """Security event severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(Enum):
    """Security event categories."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    NETWORK_ACTIVITY = "network_activity"
    SYSTEM_ACTIVITY = "system_activity"
    APPLICATION_ACTIVITY = "application_activity"
    FRAUD_DETECTION = "fraud_detection"
    COMPLIANCE = "compliance"
    THREAT_DETECTION = "threat_detection"


class IncidentStatus(Enum):
    """Security incident status."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class SecurityEvent:
    """Individual security event."""

    event_id: str
    event_type: str
    category: EventCategory
    severity: EventSeverity
    source: str
    target: str
    description: str
    details: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "category": self.category.value,
            "severity": self.severity.value,
            "source": self.source,
            "target": self.target,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }


@dataclass
class SecurityIncident:
    """Security incident record."""

    incident_id: str
    title: str
    description: str
    severity: EventSeverity
    status: IncidentStatus
    category: EventCategory
    events: List[SecurityEvent] = field(default_factory=list)
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "category": self.category.value,
            "events": [event.to_dict() for event in self.events],
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
        }


@dataclass
class AlertRule:
    """Security alert rule configuration."""

    rule_id: str
    name: str
    description: str
    event_type: str
    conditions: Dict[str, Any]
    severity_threshold: EventSeverity
    time_window: timedelta
    max_events: int
    enabled: bool = True

    def matches(self, event: SecurityEvent) -> bool:
        """Check if event matches this alert rule."""
        if self.event_type != "*" and event.event_type != self.event_type:
            return False
        severity_levels = {
            EventSeverity.INFO: 1,
            EventSeverity.LOW: 2,
            EventSeverity.MEDIUM: 3,
            EventSeverity.HIGH: 4,
            EventSeverity.CRITICAL: 5,
        }
        if severity_levels[event.severity] < severity_levels[self.severity_threshold]:
            return False
        for condition_key, condition_value in self.conditions.items():
            if condition_key == "source" and event.source != condition_value:
                return False
            elif (
                condition_key == "category" and event.category.value != condition_value
            ):
                return False
            elif condition_key == "user_id" and event.user_id != condition_value:
                return False
            elif condition_key == "ip_address" and event.ip_address != condition_value:
                return False
        return True


class SecurityMonitoringService:
    """
    Comprehensive security monitoring and incident response service.

    Features:
    - Real-time security event collection and analysis
    - Automated incident detection and creation
    - Security alerting and notification
    - Event correlation and pattern detection
    - Forensic analysis and investigation tools
    - Compliance monitoring and reporting
    - Security metrics and dashboards
    - Incident response workflow management
    """

    def __init__(self, db_client: Any, config: Dict[str, Any] = None) -> None:
        self.db = db_client
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._events = deque(maxlen=10000)
        self._incidents = {}
        self._alert_rules = {}
        self._event_handlers = {}
        self._correlation_rules = {}
        self._metrics = defaultdict(int)
        self._event_queue = asyncio.Queue()
        self._processing_task = None
        self._initialize_monitoring_service()

    def _initialize_monitoring_service(self) -> object:
        """Initialize the security monitoring service."""
        self._setup_default_alert_rules()
        self._setup_correlation_rules()
        self._register_default_handlers()
        self._start_event_processing()
        self.logger.info("Security monitoring service initialized successfully")

    def _setup_default_alert_rules(self) -> object:
        """Set up default security alert rules."""
        self._alert_rules["failed_login_attempts"] = AlertRule(
            rule_id="failed_login_attempts",
            name="Multiple Failed Login Attempts",
            description="Alert when multiple failed login attempts are detected",
            event_type="login_failed",
            conditions={"category": "authentication"},
            severity_threshold=EventSeverity.MEDIUM,
            time_window=timedelta(minutes=15),
            max_events=5,
        )
        self._alert_rules["privilege_escalation"] = AlertRule(
            rule_id="privilege_escalation",
            name="Privilege Escalation Detected",
            description="Alert when privilege escalation is detected",
            event_type="privilege_escalation",
            conditions={"category": "authorization"},
            severity_threshold=EventSeverity.HIGH,
            time_window=timedelta(minutes=5),
            max_events=1,
        )
        self._alert_rules["data_access_anomaly"] = AlertRule(
            rule_id="data_access_anomaly",
            name="Unusual Data Access Pattern",
            description="Alert when unusual data access patterns are detected",
            event_type="data_access_anomaly",
            conditions={"category": "data_access"},
            severity_threshold=EventSeverity.MEDIUM,
            time_window=timedelta(hours=1),
            max_events=10,
        )
        self._alert_rules["critical_system_events"] = AlertRule(
            rule_id="critical_system_events",
            name="Critical System Events",
            description="Alert on any critical system events",
            event_type="*",
            conditions={},
            severity_threshold=EventSeverity.CRITICAL,
            time_window=timedelta(minutes=1),
            max_events=1,
        )
        self._alert_rules["fraud_detection"] = AlertRule(
            rule_id="fraud_detection",
            name="Fraud Detection Alerts",
            description="Alert when fraud is detected",
            event_type="fraud_detected",
            conditions={"category": "fraud_detection"},
            severity_threshold=EventSeverity.HIGH,
            time_window=timedelta(minutes=1),
            max_events=1,
        )

    def _setup_correlation_rules(self) -> object:
        """Set up event correlation rules."""
        self._correlation_rules = {
            "account_takeover_pattern": {
                "description": "Detect account takeover patterns",
                "events": ["login_failed", "login_success", "password_change"],
                "time_window": timedelta(hours=1),
                "conditions": {
                    "same_user": True,
                    "different_ip": True,
                    "sequence": ["login_failed", "login_success", "password_change"],
                },
            },
            "data_exfiltration_pattern": {
                "description": "Detect data exfiltration patterns",
                "events": ["large_data_access", "file_download", "external_transfer"],
                "time_window": timedelta(minutes=30),
                "conditions": {"same_user": True, "large_volume": True},
            },
            "brute_force_pattern": {
                "description": "Detect brute force attack patterns",
                "events": ["login_failed"],
                "time_window": timedelta(minutes=15),
                "conditions": {"same_ip": True, "min_count": 10},
            },
        }

    def _register_default_handlers(self) -> object:
        """Register default event handlers."""
        self.register_event_handler("login_success", self._handle_login_success)
        self.register_event_handler("login_failed", self._handle_login_failed)
        self.register_event_handler("logout", self._handle_logout)
        self.register_event_handler("access_denied", self._handle_access_denied)
        self.register_event_handler(
            "privilege_escalation", self._handle_privilege_escalation
        )
        self.register_event_handler(
            "sensitive_data_access", self._handle_sensitive_data_access
        )
        self.register_event_handler("data_export", self._handle_data_export)
        self.register_event_handler("system_error", self._handle_system_error)
        self.register_event_handler(
            "configuration_change", self._handle_configuration_change
        )

    def _start_event_processing(self) -> object:
        """Start asynchronous event processing."""
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_events())

    async def _process_events(self):
        """Process security events from the queue."""
        while True:
            try:
                event = await self._event_queue.get()
                await self._process_single_event(event)
                self._event_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error processing security event: {str(e)}")

    async def log_security_event(
        self,
        event_type: str,
        category: EventCategory,
        severity: EventSeverity,
        source: str,
        target: str,
        description: str,
        details: Dict[str, Any] = None,
        user_id: str = None,
        session_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> SecurityEvent:
        """
        Log a security event.

        Args:
            event_type: Type of security event
            category: Event category
            severity: Event severity level
            source: Source of the event
            target: Target of the event
            description: Human-readable description
            details: Additional event details
            user_id: Associated user ID
            session_id: Associated session ID
            ip_address: Source IP address
            user_agent: User agent string

        Returns:
            SecurityEvent object
        """
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            category=category,
            severity=severity,
            source=source,
            target=target,
            description=description,
            details=details or {},
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._events.append(event)
        await self._event_queue.put(event)
        self._metrics[f"events_{category.value}"] += 1
        self._metrics[f"events_{severity.value}"] += 1
        self._metrics["total_events"] += 1
        self.logger.info(f"Security event logged: {event_type} - {severity.value}")
        return event

    async def _process_single_event(self, event: SecurityEvent):
        """Process a single security event."""
        try:
            await self._check_alert_rules(event)
            await self._correlate_events(event)
            await self._execute_event_handlers(event)
            await self._update_incident_tracking(event)
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_id}: {str(e)}")

    async def _check_alert_rules(self, event: SecurityEvent):
        """Check if event triggers any alert rules."""
        for rule_id, rule in self._alert_rules.items():
            if not rule.enabled:
                continue
            if rule.matches(event):
                recent_events = self._get_recent_events_for_rule(rule)
                if len(recent_events) >= rule.max_events:
                    await self._trigger_alert(rule, recent_events)

    def _get_recent_events_for_rule(self, rule: AlertRule) -> List[SecurityEvent]:
        """Get recent events that match the alert rule."""
        cutoff_time = datetime.now(timezone.utc) - rule.time_window
        matching_events = []
        for event in reversed(self._events):
            if event.timestamp < cutoff_time:
                break
            if rule.matches(event):
                matching_events.append(event)
        return matching_events

    async def _trigger_alert(self, rule: AlertRule, events: List[SecurityEvent]):
        """Trigger a security alert."""
        alert_data = {
            "alert_id": str(uuid.uuid4()),
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "description": rule.description,
            "severity": rule.severity_threshold.value,
            "event_count": len(events),
            "time_window": rule.time_window.total_seconds(),
            "events": [event.event_id for event in events],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._send_alert_notification(alert_data)
        await self._create_or_update_incident(rule, events)
        self.logger.warning(f"Security alert triggered: {rule.name}")

    async def _send_alert_notification(self, alert_data: Dict[str, Any]):
        """Send alert notification to configured channels."""
        self.logger.warning(f"Security alert: {json.dumps(alert_data)}")
        self._metrics["alerts_sent"] += 1

    async def _correlate_events(self, event: SecurityEvent):
        """Perform event correlation analysis."""
        for pattern_name, pattern_config in self._correlation_rules.items():
            if event.event_type in pattern_config["events"]:
                await self._check_correlation_pattern(
                    event, pattern_name, pattern_config
                )

    async def _check_correlation_pattern(
        self, event: SecurityEvent, pattern_name: str, pattern_config: Dict[str, Any]
    ):
        """Check if event matches a correlation pattern."""
        time_window = pattern_config["time_window"]
        cutoff_time = datetime.now(timezone.utc) - time_window
        recent_events = [e for e in self._events if e.timestamp >= cutoff_time]
        if pattern_name == "account_takeover_pattern":
            await self._check_account_takeover_pattern(
                event, recent_events, pattern_config
            )
        elif pattern_name == "data_exfiltration_pattern":
            await self._check_data_exfiltration_pattern(
                event, recent_events, pattern_config
            )
        elif pattern_name == "brute_force_pattern":
            await self._check_brute_force_pattern(event, recent_events, pattern_config)

    async def _check_account_takeover_pattern(
        self,
        event: SecurityEvent,
        recent_events: List[SecurityEvent],
        pattern_config: Dict[str, Any],
    ):
        """Check for account takeover patterns."""
        if not event.user_id:
            return
        user_events = [e for e in recent_events if e.user_id == event.user_id]
        failed_logins = [e for e in user_events if e.event_type == "login_failed"]
        successful_logins = [e for e in user_events if e.event_type == "login_success"]
        password_changes = [e for e in user_events if e.event_type == "password_change"]
        ip_addresses = set((e.ip_address for e in user_events if e.ip_address))
        if (
            len(failed_logins) >= 3
            and len(successful_logins) >= 1
            and (len(password_changes) >= 1)
            and (len(ip_addresses) > 1)
        ):
            await self._create_correlation_incident(
                "Account Takeover Detected",
                f"Potential account takeover for user {event.user_id}",
                EventSeverity.HIGH,
                EventCategory.AUTHENTICATION,
                user_events,
            )

    async def _check_data_exfiltration_pattern(
        self,
        event: SecurityEvent,
        recent_events: List[SecurityEvent],
        pattern_config: Dict[str, Any],
    ):
        """Check for data exfiltration patterns."""
        if not event.user_id:
            return
        user_events = [e for e in recent_events if e.user_id == event.user_id]
        data_access_events = [
            e for e in user_events if e.event_type == "large_data_access"
        ]
        download_events = [e for e in user_events if e.event_type == "file_download"]
        transfer_events = [
            e for e in user_events if e.event_type == "external_transfer"
        ]
        if len(data_access_events) >= 1 and (
            len(download_events) >= 3 or len(transfer_events) >= 1
        ):
            await self._create_correlation_incident(
                "Data Exfiltration Detected",
                f"Potential data exfiltration by user {event.user_id}",
                EventSeverity.CRITICAL,
                EventCategory.DATA_ACCESS,
                user_events,
            )

    async def _check_brute_force_pattern(
        self,
        event: SecurityEvent,
        recent_events: List[SecurityEvent],
        pattern_config: Dict[str, Any],
    ):
        """Check for brute force attack patterns."""
        if not event.ip_address:
            return
        failed_logins = [
            e
            for e in recent_events
            if e.event_type == "login_failed" and e.ip_address == event.ip_address
        ]
        min_count = pattern_config["conditions"].get("min_count", 10)
        if len(failed_logins) >= min_count:
            await self._create_correlation_incident(
                "Brute Force Attack Detected",
                f"Brute force attack from IP {event.ip_address}",
                EventSeverity.HIGH,
                EventCategory.AUTHENTICATION,
                failed_logins,
            )

    async def _create_correlation_incident(
        self,
        title: str,
        description: str,
        severity: EventSeverity,
        category: EventCategory,
        events: List[SecurityEvent],
    ):
        """Create incident from correlated events."""
        incident = SecurityIncident(
            incident_id=str(uuid.uuid4()),
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.OPEN,
            category=category,
            events=events,
        )
        self._incidents[incident.incident_id] = incident
        await self._send_alert_notification(
            {
                "alert_type": "correlation_incident",
                "incident_id": incident.incident_id,
                "title": title,
                "severity": severity.value,
                "event_count": len(events),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.logger.critical(f"Correlation incident created: {title}")

    async def _execute_event_handlers(self, event: SecurityEvent):
        """Execute registered event handlers."""
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                self.logger.error(
                    f"Error in event handler for {event.event_type}: {str(e)}"
                )

    async def _update_incident_tracking(self, event: SecurityEvent):
        """Update incident tracking based on event."""
        if event.severity == EventSeverity.CRITICAL:
            incident = SecurityIncident(
                incident_id=str(uuid.uuid4()),
                title=f"Critical Event: {event.event_type}",
                description=event.description,
                severity=event.severity,
                status=IncidentStatus.OPEN,
                category=event.category,
                events=[event],
            )
            self._incidents[incident.incident_id] = incident
            self.logger.critical(
                f"Auto-created incident for critical event: {event.event_id}"
            )

    async def _create_or_update_incident(
        self, rule: AlertRule, events: List[SecurityEvent]
    ):
        """Create or update incident based on alert rule."""
        existing_incident = None
        for incident in self._incidents.values():
            if (
                incident.status in [IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]
                and incident.category == events[0].category
            ):
                existing_incident = incident
                break
        if existing_incident:
            existing_incident.events.extend(events)
            existing_incident.updated_at = datetime.now(timezone.utc)
            existing_incident.description += (
                f"\n\nAdditional events detected by rule: {rule.name}"
            )
        else:
            incident = SecurityIncident(
                incident_id=str(uuid.uuid4()),
                title=f"Security Alert: {rule.name}",
                description=f"Incident created by alert rule: {rule.description}",
                severity=rule.severity_threshold,
                status=IncidentStatus.OPEN,
                category=events[0].category,
                events=events,
            )
            self._incidents[incident.incident_id] = incident

    def register_event_handler(self, event_type: str, handler: Callable) -> object:
        """Register a custom event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        self.logger.info(f"Registered event handler for: {event_type}")

    async def _handle_login_success(self, event: SecurityEvent):
        """Handle successful login events."""
        if event.user_id and event.ip_address:
            pass

    async def _handle_login_failed(self, event: SecurityEvent):
        """Handle failed login events."""
        if event.ip_address:
            pass

    async def _handle_logout(self, event: SecurityEvent):
        """Handle logout events."""

    async def _handle_access_denied(self, event: SecurityEvent):
        """Handle access denied events."""

    async def _handle_privilege_escalation(self, event: SecurityEvent):
        """Handle privilege escalation events."""
        incident = SecurityIncident(
            incident_id=str(uuid.uuid4()),
            title="Privilege Escalation Detected",
            description=f"Privilege escalation detected: {event.description}",
            severity=EventSeverity.HIGH,
            status=IncidentStatus.OPEN,
            category=EventCategory.AUTHORIZATION,
            events=[event],
        )
        self._incidents[incident.incident_id] = incident

    async def _handle_sensitive_data_access(self, event: SecurityEvent):
        """Handle sensitive data access events."""

    async def _handle_data_export(self, event: SecurityEvent):
        """Handle data export events."""

    async def _handle_system_error(self, event: SecurityEvent):
        """Handle system error events."""

    async def _handle_configuration_change(self, event: SecurityEvent):
        """Handle configuration change events."""

    def get_recent_events(
        self,
        limit: int = 100,
        category: EventCategory = None,
        severity: EventSeverity = None,
        time_range: timedelta = None,
    ) -> List[SecurityEvent]:
        """Get recent security events with optional filtering."""
        events = list(self._events)
        if time_range:
            cutoff_time = datetime.now(timezone.utc) - time_range
            events = [e for e in events if e.timestamp >= cutoff_time]
        if category:
            events = [e for e in events if e.category == category]
        if severity:
            events = [e for e in events if e.severity == severity]
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]

    def get_incidents(
        self,
        status: IncidentStatus = None,
        severity: EventSeverity = None,
        category: EventCategory = None,
    ) -> List[SecurityIncident]:
        """Get security incidents with optional filtering."""
        incidents = list(self._incidents.values())
        if status:
            incidents = [i for i in incidents if i.status == status]
        if severity:
            incidents = [i for i in incidents if i.severity == severity]
        if category:
            incidents = [i for i in incidents if i.category == category]
        incidents.sort(key=lambda x: x.created_at, reverse=True)
        return incidents

    def update_incident_status(
        self,
        incident_id: str,
        status: IncidentStatus,
        assigned_to: str = None,
        notes: str = None,
    ) -> bool:
        """Update incident status and assignment."""
        if incident_id not in self._incidents:
            return False
        incident = self._incidents[incident_id]
        incident.status = status
        incident.updated_at = datetime.now(timezone.utc)
        if assigned_to:
            incident.assigned_to = assigned_to
        if status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now(timezone.utc)
            incident.resolution_notes = notes
        self.logger.info(f"Updated incident {incident_id} status to {status.value}")
        return True

    def create_alert_rule(
        self,
        name: str,
        description: str,
        event_type: str,
        conditions: Dict[str, Any],
        severity_threshold: EventSeverity,
        time_window: timedelta,
        max_events: int,
    ) -> str:
        """Create a new alert rule."""
        rule_id = str(uuid.uuid4())
        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            description=description,
            event_type=event_type,
            conditions=conditions,
            severity_threshold=severity_threshold,
            time_window=time_window,
            max_events=max_events,
        )
        self._alert_rules[rule_id] = rule
        self.logger.info(f"Created alert rule: {name}")
        return rule_id

    def enable_alert_rule(self, rule_id: str) -> bool:
        """Enable an alert rule."""
        if rule_id in self._alert_rules:
            self._alert_rules[rule_id].enabled = True
            return True
        return False

    def disable_alert_rule(self, rule_id: str) -> bool:
        """Disable an alert rule."""
        if rule_id in self._alert_rules:
            self._alert_rules[rule_id].enabled = False
            return True
        return False

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security monitoring metrics."""
        open_incidents = len(
            [i for i in self._incidents.values() if i.status == IncidentStatus.OPEN]
        )
        critical_incidents = len(
            [
                i
                for i in self._incidents.values()
                if i.severity == EventSeverity.CRITICAL
            ]
        )
        now = datetime.now(timezone.utc)
        last_hour_events = len(
            [e for e in self._events if e.timestamp >= now - timedelta(hours=1)]
        )
        last_day_events = len(
            [e for e in self._events if e.timestamp >= now - timedelta(days=1)]
        )
        return {
            "total_events": self._metrics["total_events"],
            "events_last_hour": last_hour_events,
            "events_last_day": last_day_events,
            "total_incidents": len(self._incidents),
            "open_incidents": open_incidents,
            "critical_incidents": critical_incidents,
            "alerts_sent": self._metrics["alerts_sent"],
            "alert_rules": len(self._alert_rules),
            "active_alert_rules": len(
                [r for r in self._alert_rules.values() if r.enabled]
            ),
            "event_categories": {
                category.value: self._metrics.get(f"events_{category.value}", 0)
                for category in EventCategory
            },
            "event_severities": {
                severity.value: self._metrics.get(f"events_{severity.value}", 0)
                for severity in EventSeverity
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def generate_security_report(
        self, time_range: timedelta = timedelta(days=7)
    ) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        cutoff_time = datetime.now(timezone.utc) - time_range
        period_events = [e for e in self._events if e.timestamp >= cutoff_time]
        period_incidents = [
            i for i in self._incidents.values() if i.created_at >= cutoff_time
        ]
        event_stats = defaultdict(int)
        for event in period_events:
            event_stats[f"category_{event.category.value}"] += 1
            event_stats[f"severity_{event.severity.value}"] += 1
        incident_stats = defaultdict(int)
        for incident in period_incidents:
            incident_stats[f"category_{incident.category.value}"] += 1
            incident_stats[f"severity_{incident.severity.value}"] += 1
            incident_stats[f"status_{incident.status.value}"] += 1
        sources = defaultdict(int)
        targets = defaultdict(int)
        for event in period_events:
            sources[event.source] += 1
            targets[event.target] += 1
        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]
        top_targets = sorted(targets.items(), key=lambda x: x[1], reverse=True)[:10]
        return {
            "report_period": {
                "start": cutoff_time.isoformat(),
                "end": datetime.now(timezone.utc).isoformat(),
                "duration_days": time_range.days,
            },
            "summary": {
                "total_events": len(period_events),
                "total_incidents": len(period_incidents),
                "critical_events": len(
                    [e for e in period_events if e.severity == EventSeverity.CRITICAL]
                ),
                "resolved_incidents": len(
                    [i for i in period_incidents if i.status == IncidentStatus.RESOLVED]
                ),
            },
            "event_statistics": dict(event_stats),
            "incident_statistics": dict(incident_stats),
            "top_sources": top_sources,
            "top_targets": top_targets,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
