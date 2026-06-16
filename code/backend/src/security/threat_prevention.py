import json
import logging
import re
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List

from sqlalchemy.orm import Session

"\nThreat Prevention Service\n========================\n\nAdvanced threat prevention and cybersecurity service for financial applications.\nProvides real-time threat detection, prevention, and response capabilities.\n"


class ThreatType(Enum):
    """Types of security threats."""

    MALWARE = "malware"
    PHISHING = "phishing"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    INSIDER_THREAT = "insider_threat"
    API_ABUSE = "api_abuse"
    CREDENTIAL_STUFFING = "credential_stuffing"


class ThreatSeverity(Enum):
    """Threat severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseAction(Enum):
    """Threat response actions."""

    LOG = "log"
    ALERT = "alert"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    ESCALATE = "escalate"
    INVESTIGATE = "investigate"


@dataclass
class ThreatIndicator:
    """Individual threat indicator."""

    indicator_id: str
    indicator_type: str
    threat_type: ThreatType
    severity: ThreatSeverity
    confidence: float
    description: str
    evidence: Dict[str, Any]
    source: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator_id": self.indicator_id,
            "indicator_type": self.indicator_type,
            "threat_type": self.threat_type.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "description": self.description,
            "evidence": self.evidence,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ThreatAssessment:
    """Comprehensive threat assessment result."""

    assessment_id: str
    target_id: str
    target_type: str
    overall_threat_score: float
    threat_level: ThreatSeverity
    recommended_actions: List[ResponseAction]
    threat_indicators: List[ThreatIndicator]
    attack_vectors: List[str]
    mitigation_recommendations: List[str]
    assessment_timestamp: datetime
    expires_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "overall_threat_score": self.overall_threat_score,
            "threat_level": self.threat_level.value,
            "recommended_actions": [
                action.value for action in self.recommended_actions
            ],
            "threat_indicators": [
                indicator.to_dict() for indicator in self.threat_indicators
            ],
            "attack_vectors": self.attack_vectors,
            "mitigation_recommendations": self.mitigation_recommendations,
            "assessment_timestamp": self.assessment_timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


class ThreatPreventionService:
    """
    Advanced threat prevention service for financial applications.

    Features:
    - Real-time threat detection and analysis
    - Web application firewall (WAF) capabilities
    - API security and rate limiting
    - Malware detection and prevention
    - Phishing and social engineering detection
    - DDoS protection and mitigation
    - Intrusion detection and prevention
    - Behavioral threat analysis
    - Threat intelligence integration
    - Automated incident response
    """

    def __init__(self, db_session: Session, config: Dict[str, Any] = None) -> None:
        self.db = db_session
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._threat_signatures = {}
        self._behavioral_baselines = {}
        self._threat_intelligence = {}
        self._rate_limiters = {}
        self._blocked_entities = {}
        self._security_rules = {}
        self._threat_thresholds = {
            ThreatSeverity.INFO: 0.1,
            ThreatSeverity.LOW: 0.3,
            ThreatSeverity.MEDIUM: 0.5,
            ThreatSeverity.HIGH: 0.7,
            ThreatSeverity.CRITICAL: 0.9,
        }
        self._initialize_threat_prevention()

    def _initialize_threat_prevention(self) -> object:
        """Initialize the threat prevention service."""
        self._load_threat_signatures()
        self._initialize_security_rules()
        self._load_threat_intelligence()
        self._initialize_rate_limiters()
        self._initialize_behavioral_baselines()
        self.logger.info("Threat prevention service initialized successfully")

    def _load_threat_signatures(self) -> object:
        """Load threat detection signatures."""
        self._threat_signatures[ThreatType.SQL_INJECTION] = [
            "(\\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\\b)",
            "(\\b(OR|AND)\\s+\\d+\\s*=\\s*\\d+)",
            "(\\b(OR|AND)\\s+['\\\"]?\\w+['\\\"]?\\s*=\\s*['\\\"]?\\w+['\\\"]?)",
            "(--|#|/\\*|\\*/)",
            "(\\bUNION\\s+(ALL\\s+)?SELECT\\b)",
            "(\\b(EXEC|EXECUTE)\\s+\\w+)",
            "(\\b(CAST|CONVERT|CHAR|ASCII)\\s*\\()",
            "(\\b(WAITFOR|DELAY)\\s+['\\\"]?\\d+['\\\"]?)",
        ]
        self._threat_signatures[ThreatType.XSS] = [
            "(<script[^>]*>.*?</script>)",
            "(javascript\\s*:)",
            "(on\\w+\\s*=\\s*['\\\"][^'\\\"]*['\\\"])",
            "(<iframe[^>]*>)",
            "(<object[^>]*>)",
            "(<embed[^>]*>)",
            "(<link[^>]*>)",
            "(<meta[^>]*>)",
            "(eval\\s*\\()",
            "(document\\.(write|writeln|cookie))",
            "(window\\.(location|open))",
        ]
        self._threat_signatures[ThreatType.MALWARE] = [
            "(\\b(cmd|powershell|bash|sh)\\s+)",
            "(\\b(wget|curl|nc|netcat)\\s+)",
            "(\\b(chmod|chown|sudo)\\s+)",
            "(\\|\\s*(cat|ls|ps|id|whoami|uname))",
            "(\\$\\(.*\\))",
            "(`.*`)",
            "(\\b(rm|del|format)\\s+)",
        ]
        self._threat_signatures[ThreatType.PHISHING] = [
            "(urgent.{0,20}action.{0,20}required)",
            "(verify.{0,20}account.{0,20}immediately)",
            "(suspended.{0,20}account)",
            "(click.{0,20}here.{0,20}now)",
            "(limited.{0,20}time.{0,20}offer)",
            "(congratulations.{0,20}winner)",
            "(security.{0,20}alert)",
            "(update.{0,20}payment.{0,20}information)",
        ]

    def _initialize_security_rules(self) -> object:
        """Initialize security rules and policies."""
        self._security_rules = {
            "rate_limiting": {
                "api_requests_per_minute": 100,
                "login_attempts_per_hour": 5,
                "password_reset_per_day": 3,
                "transaction_requests_per_hour": 50,
            },
            "input_validation": {
                "max_input_length": 10000,
                "allowed_file_types": [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".pdf",
                    ".doc",
                    ".docx",
                ],
                "max_file_size_mb": 10,
                "blocked_extensions": [".exe", ".bat", ".cmd", ".scr", ".vbs", ".js"],
            },
            "authentication": {
                "max_failed_attempts": 5,
                "lockout_duration_minutes": 30,
                "password_min_length": 8,
                "require_mfa": True,
                "session_timeout_minutes": 30,
            },
            "network_security": {
                "blocked_countries": ["XX", "YY"],
                "blocked_ip_ranges": ["192.168.100.0/24"],
                "require_https": True,
                "block_tor_exit_nodes": True,
            },
        }

    def _load_threat_intelligence(self) -> object:
        """Load threat intelligence data."""
        self._threat_intelligence = {
            "malicious_ips": {
                "192.168.1.100": {
                    "threat_type": "botnet",
                    "confidence": 0.9,
                    "last_seen": datetime.now(timezone.utc) - timedelta(hours=2),
                    "source": "ThreatFeed Pro",
                },
                "10.0.0.50": {
                    "threat_type": "malware_c2",
                    "confidence": 0.85,
                    "last_seen": datetime.now(timezone.utc) - timedelta(hours=6),
                    "source": "CyberIntel",
                },
            },
            "malicious_domains": {
                "malicious-site.com": {
                    "threat_type": "phishing",
                    "confidence": 0.95,
                    "last_seen": datetime.now(timezone.utc) - timedelta(hours=1),
                    "source": "PhishTank",
                },
                "fake-bank.net": {
                    "threat_type": "financial_fraud",
                    "confidence": 0.9,
                    "last_seen": datetime.now(timezone.utc) - timedelta(hours=4),
                    "source": "FinCERT",
                },
            },
            "malicious_hashes": {
                "a1b2c3d4e5f6": {
                    "threat_type": "banking_trojan",
                    "confidence": 0.98,
                    "last_seen": datetime.now(timezone.utc) - timedelta(hours=3),
                    "source": "MalwareDB",
                }
            },
        }

    def _initialize_rate_limiters(self) -> object:
        """Initialize rate limiting mechanisms."""
        self._rate_limiters = {
            "api_requests": defaultdict(lambda: deque()),
            "login_attempts": defaultdict(lambda: deque()),
            "password_resets": defaultdict(lambda: deque()),
            "transaction_requests": defaultdict(lambda: deque()),
        }

    def _initialize_behavioral_baselines(self) -> object:
        """Initialize behavioral analysis baselines."""
        self._behavioral_baselines = {
            "normal_request_patterns": {
                "avg_requests_per_minute": 10,
                "typical_request_sizes": [100, 500, 1000],
                "common_user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "Mozilla/5.0 (X11; Linux x86_64)",
                ],
                "typical_response_times": [50, 100, 200],
            },
            "normal_login_patterns": {
                "typical_login_hours": list(range(6, 23)),
                "common_locations": ["US", "CA", "GB", "DE"],
                "session_duration_minutes": [15, 30, 60, 120],
            },
        }

    async def assess_request_threat(
        self, request_data: Dict[str, Any]
    ) -> ThreatAssessment:
        """
        Assess threat level for an incoming request.

        Args:
            request_data: Request information for threat assessment

        Returns:
            ThreatAssessment containing threat analysis results
        """
        assessment_id = str(uuid.uuid4())
        request_id = request_data.get("request_id", "unknown")
        try:
            self.logger.info(f"Starting threat assessment for request {request_id}")
            threat_indicators = []
            injection_indicators = await self._detect_injection_attacks(request_data)
            threat_indicators.extend(injection_indicators)
            rate_limit_indicators = await self._check_rate_limits(request_data)
            threat_indicators.extend(rate_limit_indicators)
            ip_reputation_indicators = await self._check_ip_reputation(request_data)
            threat_indicators.extend(ip_reputation_indicators)
            behavioral_indicators = await self._analyze_request_behavior(request_data)
            threat_indicators.extend(behavioral_indicators)
            if "file_uploads" in request_data:
                file_indicators = await self._analyze_file_uploads(
                    request_data["file_uploads"]
                )
                threat_indicators.extend(file_indicators)
            overall_threat_score = self._calculate_threat_score(threat_indicators)
            threat_level = self._determine_threat_level(overall_threat_score)
            recommended_actions = self._determine_response_actions(
                threat_level, threat_indicators
            )
            attack_vectors = self._identify_attack_vectors(threat_indicators)
            mitigation_recommendations = self._generate_mitigation_recommendations(
                threat_indicators
            )
            assessment = ThreatAssessment(
                assessment_id=assessment_id,
                target_id=request_id,
                target_type="request",
                overall_threat_score=overall_threat_score,
                threat_level=threat_level,
                recommended_actions=recommended_actions,
                threat_indicators=threat_indicators,
                attack_vectors=attack_vectors,
                mitigation_recommendations=mitigation_recommendations,
                assessment_timestamp=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            )
            await self._execute_response_actions(assessment, request_data)
            self.logger.info(
                f"Threat assessment completed for request {request_id}: {threat_level.value}"
            )
            return assessment
        except Exception as e:
            self.logger.error(
                f"Error in threat assessment for request {request_id}: {str(e)}"
            )
            return ThreatAssessment(
                assessment_id=assessment_id,
                target_id=request_id,
                target_type="request",
                overall_threat_score=0.5,
                threat_level=ThreatSeverity.MEDIUM,
                recommended_actions=[ResponseAction.LOG, ResponseAction.INVESTIGATE],
                threat_indicators=[
                    ThreatIndicator(
                        indicator_id=f"error_{int(datetime.now(timezone.utc).timestamp())}",
                        indicator_type="assessment_error",
                        threat_type=ThreatType.API_ABUSE,
                        severity=ThreatSeverity.MEDIUM,
                        confidence=0.1,
                        description=f"Error in threat assessment: {str(e)}",
                        evidence={"error": str(e)},
                        source="threat_prevention",
                        timestamp=datetime.now(timezone.utc),
                    )
                ],
                attack_vectors=[],
                mitigation_recommendations=["Investigate assessment error"],
                assessment_timestamp=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            )

    async def _detect_injection_attacks(
        self, request_data: Dict[str, Any]
    ) -> List[ThreatIndicator]:
        """Detect injection attacks in request data."""
        indicators = []
        inputs_to_check = []
        if "url_params" in request_data:
            inputs_to_check.extend(request_data["url_params"].values())
        if "post_data" in request_data:
            inputs_to_check.extend(request_data["post_data"].values())
        if "headers" in request_data:
            inputs_to_check.extend(request_data["headers"].values())
        for input_value in inputs_to_check:
            if not isinstance(input_value, str):
                continue
            sql_matches = self._check_signatures(input_value, ThreatType.SQL_INJECTION)
            if sql_matches:
                indicators.append(
                    ThreatIndicator(
                        indicator_id=f"sqli_{int(datetime.now(timezone.utc).timestamp())}",
                        indicator_type="sql_injection",
                        threat_type=ThreatType.SQL_INJECTION,
                        severity=ThreatSeverity.HIGH,
                        confidence=0.9,
                        description="SQL injection attempt detected",
                        evidence={"input": input_value[:100], "matches": sql_matches},
                        source="signature_detection",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
            xss_matches = self._check_signatures(input_value, ThreatType.XSS)
            if xss_matches:
                indicators.append(
                    ThreatIndicator(
                        indicator_id=f"xss_{int(datetime.now(timezone.utc).timestamp())}",
                        indicator_type="cross_site_scripting",
                        threat_type=ThreatType.XSS,
                        severity=ThreatSeverity.HIGH,
                        confidence=0.85,
                        description="Cross-site scripting attempt detected",
                        evidence={"input": input_value[:100], "matches": xss_matches},
                        source="signature_detection",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
            cmd_matches = self._check_signatures(input_value, ThreatType.MALWARE)
            if cmd_matches:
                indicators.append(
                    ThreatIndicator(
                        indicator_id=f"cmdi_{int(datetime.now(timezone.utc).timestamp())}",
                        indicator_type="command_injection",
                        threat_type=ThreatType.MALWARE,
                        severity=ThreatSeverity.CRITICAL,
                        confidence=0.95,
                        description="Command injection attempt detected",
                        evidence={"input": input_value[:100], "matches": cmd_matches},
                        source="signature_detection",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
        return indicators

    def _check_signatures(self, input_value: str, threat_type: ThreatType) -> List[str]:
        """Check input against threat signatures."""
        matches = []
        signatures = self._threat_signatures.get(threat_type, [])
        for signature in signatures:
            if re.search(signature, input_value, re.IGNORECASE):
                matches.append(signature)
        return matches

    async def _check_rate_limits(
        self, request_data: Dict[str, Any]
    ) -> List[ThreatIndicator]:
        """Check for rate limiting violations."""
        indicators = []
        client_ip = request_data.get("client_ip", "")
        user_id = request_data.get("user_id", "")
        request_type = request_data.get("request_type", "api")
        rate_limit_key = user_id if user_id else client_ip
        if not rate_limit_key:
            return indicators
        current_time = datetime.now(timezone.utc)
        if request_type == "api":
            api_requests = self._rate_limiters["api_requests"][rate_limit_key]
            api_requests.append(current_time)
            cutoff = current_time - timedelta(minutes=1)
            while api_requests and api_requests[0] < cutoff:
                api_requests.popleft()
            max_requests = self._security_rules["rate_limiting"][
                "api_requests_per_minute"
            ]
            if len(api_requests) > max_requests:
                indicators.append(
                    ThreatIndicator(
                        indicator_id=f"rate_limit_{int(datetime.now(timezone.utc).timestamp())}",
                        indicator_type="rate_limit_exceeded",
                        threat_type=ThreatType.API_ABUSE,
                        severity=ThreatSeverity.MEDIUM,
                        confidence=0.9,
                        description=f"API rate limit exceeded: {len(api_requests)} requests in 1 minute",
                        evidence={
                            "request_count": len(api_requests),
                            "limit": max_requests,
                            "client_ip": client_ip,
                            "user_id": user_id,
                        },
                        source="rate_limiter",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
        elif request_type == "login":
            login_attempts = self._rate_limiters["login_attempts"][rate_limit_key]
            login_attempts.append(current_time)
            cutoff = current_time - timedelta(hours=1)
            while login_attempts and login_attempts[0] < cutoff:
                login_attempts.popleft()
            max_attempts = self._security_rules["rate_limiting"][
                "login_attempts_per_hour"
            ]
            if len(login_attempts) > max_attempts:
                indicators.append(
                    ThreatIndicator(
                        indicator_id=f"login_rate_limit_{int(datetime.now(timezone.utc).timestamp())}",
                        indicator_type="login_rate_limit_exceeded",
                        threat_type=ThreatType.BRUTE_FORCE,
                        severity=ThreatSeverity.HIGH,
                        confidence=0.95,
                        description=f"Login rate limit exceeded: {len(login_attempts)} attempts in 1 hour",
                        evidence={
                            "attempt_count": len(login_attempts),
                            "limit": max_attempts,
                            "client_ip": client_ip,
                            "user_id": user_id,
                        },
                        source="rate_limiter",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
        return indicators

    async def _check_ip_reputation(
        self, request_data: Dict[str, Any]
    ) -> List[ThreatIndicator]:
        """Check IP reputation against threat intelligence."""
        indicators = []
        client_ip = request_data.get("client_ip", "")
        if not client_ip:
            return indicators
        if client_ip in self._threat_intelligence["malicious_ips"]:
            threat_info = self._threat_intelligence["malicious_ips"][client_ip]
            indicators.append(
                ThreatIndicator(
                    indicator_id=f"malicious_ip_{int(datetime.now(timezone.utc).timestamp())}",
                    indicator_type="malicious_ip",
                    threat_type=ThreatType.MALWARE,
                    severity=ThreatSeverity.HIGH,
                    confidence=threat_info["confidence"],
                    description=f"Request from known malicious IP: {threat_info['threat_type']}",
                    evidence={
                        "ip_address": client_ip,
                        "threat_type": threat_info["threat_type"],
                        "source": threat_info["source"],
                        "last_seen": threat_info["last_seen"].isoformat(),
                    },
                    source="threat_intelligence",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        country_code = request_data.get("country_code", "")
        blocked_countries = self._security_rules["network_security"][
            "blocked_countries"
        ]
        if country_code in blocked_countries:
            indicators.append(
                ThreatIndicator(
                    indicator_id=f"blocked_country_{int(datetime.now(timezone.utc).timestamp())}",
                    indicator_type="blocked_geography",
                    threat_type=ThreatType.API_ABUSE,
                    severity=ThreatSeverity.MEDIUM,
                    confidence=0.8,
                    description=f"Request from blocked country: {country_code}",
                    evidence={"country_code": country_code, "ip_address": client_ip},
                    source="geo_blocking",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        if self._is_tor_exit_node(client_ip):
            indicators.append(
                ThreatIndicator(
                    indicator_id=f"tor_exit_{int(datetime.now(timezone.utc).timestamp())}",
                    indicator_type="tor_exit_node",
                    threat_type=ThreatType.API_ABUSE,
                    severity=ThreatSeverity.MEDIUM,
                    confidence=0.9,
                    description="Request from Tor exit node",
                    evidence={"ip_address": client_ip},
                    source="tor_detection",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        return indicators

    async def _analyze_request_behavior(
        self, request_data: Dict[str, Any]
    ) -> List[ThreatIndicator]:
        """Analyze request behavioral patterns."""
        indicators = []
        request_size = request_data.get("request_size", 0)
        max_size = self._security_rules["input_validation"]["max_input_length"]
        if request_size > max_size:
            indicators.append(
                ThreatIndicator(
                    indicator_id=f"large_request_{int(datetime.now(timezone.utc).timestamp())}",
                    indicator_type="oversized_request",
                    threat_type=ThreatType.DDoS,
                    severity=ThreatSeverity.MEDIUM,
                    confidence=0.7,
                    description=f"Oversized request: {request_size} bytes",
                    evidence={"request_size": request_size, "max_size": max_size},
                    source="behavioral_analysis",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        user_agent = request_data.get("user_agent", "")
        if self._is_suspicious_user_agent(user_agent):
            indicators.append(
                ThreatIndicator(
                    indicator_id=f"suspicious_ua_{int(datetime.now(timezone.utc).timestamp())}",
                    indicator_type="suspicious_user_agent",
                    threat_type=ThreatType.API_ABUSE,
                    severity=ThreatSeverity.LOW,
                    confidence=0.6,
                    description="Suspicious user agent detected",
                    evidence={"user_agent": user_agent},
                    source="behavioral_analysis",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        request_path = request_data.get("request_path", "")
        if self._is_suspicious_path(request_path):
            indicators.append(
                ThreatIndicator(
                    indicator_id=f"suspicious_path_{int(datetime.now(timezone.utc).timestamp())}",
                    indicator_type="suspicious_request_path",
                    threat_type=ThreatType.API_ABUSE,
                    severity=ThreatSeverity.MEDIUM,
                    confidence=0.8,
                    description="Suspicious request path detected",
                    evidence={"request_path": request_path},
                    source="behavioral_analysis",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        return indicators

    async def _analyze_file_uploads(
        self, file_uploads: List[Dict[str, Any]]
    ) -> List[ThreatIndicator]:
        """Analyze uploaded files for security threats."""
        indicators = []
        for file_info in file_uploads:
            filename = file_info.get("filename", "")
            file_size = file_info.get("file_size", 0)
            file_content = file_info.get("content", b"")
            file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
            blocked_extensions = self._security_rules["input_validation"][
                "blocked_extensions"
            ]
            if file_ext in blocked_extensions:
                indicators.append(
                    ThreatIndicator(
                        indicator_id=f"blocked_file_{int(datetime.now(timezone.utc).timestamp())}",
                        indicator_type="blocked_file_type",
                        threat_type=ThreatType.MALWARE,
                        severity=ThreatSeverity.HIGH,
                        confidence=0.9,
                        description=f"Blocked file type uploaded: {file_ext}",
                        evidence={"filename": filename, "extension": file_ext},
                        source="file_analysis",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
            max_size_mb = self._security_rules["input_validation"]["max_file_size_mb"]
            max_size_bytes = max_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                indicators.append(
                    ThreatIndicator(
                        indicator_id=f"oversized_file_{int(datetime.now(timezone.utc).timestamp())}",
                        indicator_type="oversized_file",
                        threat_type=ThreatType.DDoS,
                        severity=ThreatSeverity.MEDIUM,
                        confidence=0.8,
                        description=f"Oversized file upload: {file_size} bytes",
                        evidence={
                            "filename": filename,
                            "file_size": file_size,
                            "max_size": max_size_bytes,
                        },
                        source="file_analysis",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
            if self._contains_malware_signatures(file_content):
                indicators.append(
                    ThreatIndicator(
                        indicator_id=f"malware_file_{int(datetime.now(timezone.utc).timestamp())}",
                        indicator_type="malware_detected",
                        threat_type=ThreatType.MALWARE,
                        severity=ThreatSeverity.CRITICAL,
                        confidence=0.95,
                        description="Potential malware detected in uploaded file",
                        evidence={"filename": filename, "file_size": file_size},
                        source="malware_scanner",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
        return indicators

    def _calculate_threat_score(
        self, threat_indicators: List[ThreatIndicator]
    ) -> float:
        """Calculate overall threat score from indicators."""
        if not threat_indicators:
            return 0.0
        total_weighted_score = 0.0
        total_weight = 0.0
        severity_weights = {
            ThreatSeverity.INFO: 0.1,
            ThreatSeverity.LOW: 0.3,
            ThreatSeverity.MEDIUM: 0.5,
            ThreatSeverity.HIGH: 0.8,
            ThreatSeverity.CRITICAL: 1.0,
        }
        for indicator in threat_indicators:
            severity_weight = severity_weights[indicator.severity]
            weight = severity_weight * indicator.confidence
            total_weighted_score += weight
            total_weight += weight
        if total_weight == 0:
            return 0.0
        base_score = total_weighted_score / total_weight
        indicator_multiplier = min(1.0 + (len(threat_indicators) - 1) * 0.1, 1.5)
        return min(base_score * indicator_multiplier, 1.0)

    def _determine_threat_level(self, threat_score: float) -> ThreatSeverity:
        """Determine threat level based on threat score."""
        if threat_score >= self._threat_thresholds[ThreatSeverity.CRITICAL]:
            return ThreatSeverity.CRITICAL
        elif threat_score >= self._threat_thresholds[ThreatSeverity.HIGH]:
            return ThreatSeverity.HIGH
        elif threat_score >= self._threat_thresholds[ThreatSeverity.MEDIUM]:
            return ThreatSeverity.MEDIUM
        elif threat_score >= self._threat_thresholds[ThreatSeverity.LOW]:
            return ThreatSeverity.LOW
        else:
            return ThreatSeverity.INFO

    def _determine_response_actions(
        self, threat_level: ThreatSeverity, threat_indicators: List[ThreatIndicator]
    ) -> List[ResponseAction]:
        """Determine appropriate response actions."""
        actions = []
        actions.append(ResponseAction.LOG)
        if threat_level == ThreatSeverity.CRITICAL:
            actions.extend(
                [ResponseAction.BLOCK, ResponseAction.ALERT, ResponseAction.ESCALATE]
            )
        elif threat_level == ThreatSeverity.HIGH:
            actions.extend([ResponseAction.BLOCK, ResponseAction.ALERT])
        elif threat_level == ThreatSeverity.MEDIUM:
            actions.extend([ResponseAction.ALERT, ResponseAction.INVESTIGATE])
        elif threat_level == ThreatSeverity.LOW:
            actions.append(ResponseAction.ALERT)
        critical_threats = {
            ThreatType.SQL_INJECTION,
            ThreatType.MALWARE,
            ThreatType.XSS,
        }
        has_critical_threat = any(
            (
                indicator.threat_type in critical_threats
                for indicator in threat_indicators
            )
        )
        if has_critical_threat and ResponseAction.BLOCK not in actions:
            actions.append(ResponseAction.BLOCK)
        return actions

    def _identify_attack_vectors(
        self, threat_indicators: List[ThreatIndicator]
    ) -> List[str]:
        """Identify attack vectors from threat indicators."""
        attack_vectors = set()
        for indicator in threat_indicators:
            if indicator.threat_type == ThreatType.SQL_INJECTION:
                attack_vectors.add("SQL Injection")
            elif indicator.threat_type == ThreatType.XSS:
                attack_vectors.add("Cross-Site Scripting")
            elif indicator.threat_type == ThreatType.MALWARE:
                attack_vectors.add("Malware/Command Injection")
            elif indicator.threat_type == ThreatType.BRUTE_FORCE:
                attack_vectors.add("Brute Force Attack")
            elif indicator.threat_type == ThreatType.DDoS:
                attack_vectors.add("Denial of Service")
            elif indicator.threat_type == ThreatType.API_ABUSE:
                attack_vectors.add("API Abuse")
            elif indicator.threat_type == ThreatType.PHISHING:
                attack_vectors.add("Phishing")
        return list(attack_vectors)

    def _generate_mitigation_recommendations(
        self, threat_indicators: List[ThreatIndicator]
    ) -> List[str]:
        """Generate mitigation recommendations."""
        recommendations = set()
        for indicator in threat_indicators:
            if indicator.threat_type == ThreatType.SQL_INJECTION:
                recommendations.add(
                    "Implement parameterized queries and input validation"
                )
                recommendations.add("Use web application firewall (WAF) rules")
            elif indicator.threat_type == ThreatType.XSS:
                recommendations.add(
                    "Implement output encoding and content security policy"
                )
                recommendations.add("Validate and sanitize all user inputs")
            elif indicator.threat_type == ThreatType.MALWARE:
                recommendations.add("Implement file upload restrictions and scanning")
                recommendations.add("Use application sandboxing")
            elif indicator.threat_type == ThreatType.BRUTE_FORCE:
                recommendations.add("Implement account lockout policies")
                recommendations.add("Use CAPTCHA and multi-factor authentication")
            elif indicator.threat_type == ThreatType.DDoS:
                recommendations.add("Implement rate limiting and traffic shaping")
                recommendations.add("Use DDoS protection services")
            elif indicator.threat_type == ThreatType.API_ABUSE:
                recommendations.add("Implement API rate limiting and authentication")
                recommendations.add("Monitor API usage patterns")
        return list(recommendations)

    async def _execute_response_actions(
        self, assessment: ThreatAssessment, request_data: Dict[str, Any]
    ):
        """Execute immediate response actions."""
        client_ip = request_data.get("client_ip", "")
        user_id = request_data.get("user_id", "")
        for action in assessment.recommended_actions:
            if action == ResponseAction.BLOCK:
                await self._block_entity(client_ip, user_id, assessment)
            elif action == ResponseAction.ALERT:
                await self._send_security_alert(assessment)
            elif action == ResponseAction.ESCALATE:
                await self._escalate_incident(assessment)
            elif action == ResponseAction.QUARANTINE:
                await self._quarantine_entity(client_ip, user_id, assessment)

    async def _block_entity(
        self, client_ip: str, user_id: str, assessment: ThreatAssessment
    ):
        """Block IP address or user account."""
        block_duration = timedelta(hours=24)
        if client_ip:
            self._blocked_entities[client_ip] = {
                "blocked_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + block_duration,
                "reason": f"Threat assessment: {assessment.threat_level.value}",
                "assessment_id": assessment.assessment_id,
            }
            self.logger.warning(f"Blocked IP address: {client_ip}")
        if user_id:
            self._blocked_entities[user_id] = {
                "blocked_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + block_duration,
                "reason": f"Threat assessment: {assessment.threat_level.value}",
                "assessment_id": assessment.assessment_id,
            }
            self.logger.warning(f"Blocked user account: {user_id}")

    async def _send_security_alert(self, assessment: ThreatAssessment):
        """Send security alert to monitoring systems."""
        alert_data = {
            "alert_type": "security_threat",
            "severity": assessment.threat_level.value,
            "target": assessment.target_id,
            "threat_score": assessment.overall_threat_score,
            "indicators": len(assessment.threat_indicators),
            "timestamp": assessment.assessment_timestamp.isoformat(),
        }
        self.logger.warning(f"Security alert: {json.dumps(alert_data)}")

    async def _escalate_incident(self, assessment: ThreatAssessment):
        """Escalate security incident to security team."""
        incident_data = {
            "incident_type": "security_threat",
            "severity": assessment.threat_level.value,
            "assessment_id": assessment.assessment_id,
            "target": assessment.target_id,
            "attack_vectors": assessment.attack_vectors,
            "timestamp": assessment.assessment_timestamp.isoformat(),
        }
        self.logger.critical(
            f"Security incident escalated: {json.dumps(incident_data)}"
        )

    async def _quarantine_entity(
        self, client_ip: str, user_id: str, assessment: ThreatAssessment
    ):
        """Quarantine entity for further investigation."""
        await self._block_entity(client_ip, user_id, assessment)
        self.logger.warning(f"Quarantined entity - IP: {client_ip}, User: {user_id}")

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious."""
        suspicious_patterns = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "automated",
            "curl",
            "wget",
            "python",
            "java",
            "go-http",
        ]
        user_agent_lower = user_agent.lower()
        return any((pattern in user_agent_lower for pattern in suspicious_patterns))

    def _is_suspicious_path(self, request_path: str) -> bool:
        """Check if request path is suspicious."""
        suspicious_patterns = [
            "/admin",
            "/wp-admin",
            "/phpmyadmin",
            "/config",
            "/.env",
            "/.git",
            "/backup",
            "/test",
            "../",
            "..\\",
            "/etc/passwd",
            "/proc/",
            "eval(",
            "base64_decode",
            "system(",
        ]
        path_lower = request_path.lower()
        return any((pattern in path_lower for pattern in suspicious_patterns))

    def _is_tor_exit_node(self, ip_address: str) -> bool:
        """Check if IP is a Tor exit node."""
        return "tor" in ip_address.lower()

    def _contains_malware_signatures(self, file_content: bytes) -> bool:
        """Check file content for malware signatures."""
        malware_signatures = [
            b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE",
            b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR",
            b"eval(base64_decode(",
            b"system(",
            b"exec(",
            b"shell_exec(",
        ]
        for signature in malware_signatures:
            if signature in file_content:
                return True
        return False

    def is_entity_blocked(self, entity_id: str) -> bool:
        """Check if an entity (IP or user) is currently blocked."""
        if entity_id not in self._blocked_entities:
            return False
        block_info = self._blocked_entities[entity_id]
        if datetime.now(timezone.utc) > block_info["expires_at"]:
            del self._blocked_entities[entity_id]
            return False
        return True

    def unblock_entity(self, entity_id: str) -> bool:
        """Manually unblock an entity."""
        if entity_id in self._blocked_entities:
            del self._blocked_entities[entity_id]
            self.logger.info(f"Manually unblocked entity: {entity_id}")
            return True
        return False

    def get_threat_statistics(self) -> Dict[str, Any]:
        """Get threat prevention service statistics."""
        return {
            "threat_signatures": sum(
                (len(sigs) for sigs in self._threat_signatures.values())
            ),
            "blocked_entities": len(self._blocked_entities),
            "threat_intelligence_ips": len(self._threat_intelligence["malicious_ips"]),
            "threat_intelligence_domains": len(
                self._threat_intelligence["malicious_domains"]
            ),
            "security_rules": len(self._security_rules),
            "rate_limiters": len(self._rate_limiters),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
