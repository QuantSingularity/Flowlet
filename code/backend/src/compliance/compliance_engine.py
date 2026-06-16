import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .aml_engine import AMLEngine, AMLResult
from .audit_service import ComplianceAuditService
from .data_protection import DataProtectionService
from .kyc_service import KYCService
from .regulatory_framework import ComplianceRule, Jurisdiction, RegulatoryFramework
from .reporting_service import ComplianceReportingService

"\nCompliance Engine\n================\n\nCentral compliance engine for multi-jurisdiction regulatory compliance.\nOrchestrates all compliance activities including AML, KYC, data protection, and reporting.\n"


class ComplianceStatus(Enum):
    """Compliance status levels."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    REQUIRES_ACTION = "requires_action"
    UNKNOWN = "unknown"


class ComplianceSeverity(Enum):
    """Compliance issue severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceCheck:
    """Individual compliance check result."""

    check_id: str
    rule_id: str
    jurisdiction: Jurisdiction
    status: ComplianceStatus
    severity: ComplianceSeverity
    description: str
    details: Dict[str, Any]
    timestamp: datetime
    remediation_required: bool = False
    remediation_deadline: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "rule_id": self.rule_id,
            "jurisdiction": self.jurisdiction.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "remediation_required": self.remediation_required,
            "remediation_deadline": (
                self.remediation_deadline.isoformat()
                if self.remediation_deadline
                else None
            ),
        }


@dataclass
class ComplianceAssessment:
    """Overall compliance assessment result."""

    assessment_id: str
    entity_id: str
    entity_type: str
    jurisdictions: List[Jurisdiction]
    overall_status: ComplianceStatus
    checks: List[ComplianceCheck]
    risk_score: float
    timestamp: datetime
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "jurisdictions": [j.value for j in self.jurisdictions],
            "overall_status": self.overall_status.value,
            "checks": [check.to_dict() for check in self.checks],
            "risk_score": self.risk_score,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class ComplianceEngine:
    """
    Central compliance engine for multi-jurisdiction regulatory compliance.

    Features:
    - Multi-jurisdiction compliance orchestration
    - Real-time compliance monitoring
    - Automated rule evaluation
    - Risk-based compliance assessment
    - Regulatory reporting automation
    - Audit trail management
    - Remediation workflow management
    """

    def __init__(self, db_session: Session, config: Dict[str, Any] = None) -> None:
        self.db = db_session
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.regulatory_framework = RegulatoryFramework()
        self.aml_engine = AMLEngine(db_session)
        self.kyc_service = KYCService(db_session)
        self.data_protection = DataProtectionService(db_session)
        self.reporting_service = ComplianceReportingService(db_session)
        self.audit_service = ComplianceAuditService(db_session)
        self._active_assessments = {}
        self._compliance_cache = {}
        self._monitoring_enabled = True
        self.logger.info("Compliance engine initialized")

    async def assess_compliance(
        self,
        entity_id: str,
        entity_type: str,
        jurisdictions: List[Jurisdiction] = None,
        force_refresh: bool = False,
    ) -> ComplianceAssessment:
        """
        Perform comprehensive compliance assessment for an entity.

        Args:
            entity_id: Unique identifier of the entity
            entity_type: Type of entity (user, transaction, merchant, etc.)
            jurisdictions: List of jurisdictions to assess against
            force_refresh: Force fresh assessment ignoring cache

        Returns:
            ComplianceAssessment containing detailed compliance status
        """
        assessment_id = (
            f"{entity_type}_{entity_id}_{int(datetime.now(timezone.utc).timestamp())}"
        )
        if jurisdictions is None:
            jurisdictions = [Jurisdiction.EU, Jurisdiction.US, Jurisdiction.SINGAPORE]
        cache_key = f"{entity_type}_{entity_id}_{hash(tuple(jurisdictions))}"
        if not force_refresh and cache_key in self._compliance_cache:
            cached_assessment = self._compliance_cache[cache_key]
            if (
                cached_assessment.expires_at
                and cached_assessment.expires_at > datetime.now(timezone.utc)
            ):
                self.logger.debug(
                    f"Returning cached compliance assessment for {entity_id}"
                )
                return cached_assessment
        try:
            self.logger.info(
                f"Starting compliance assessment for {entity_type} {entity_id}"
            )
            entity_data = await self._get_entity_data(entity_id, entity_type)
            all_checks = []
            overall_risk_score = 0.0
            for jurisdiction in jurisdictions:
                jurisdiction_checks = await self._assess_jurisdiction_compliance(
                    entity_id, entity_type, entity_data, jurisdiction
                )
                all_checks.extend(jurisdiction_checks)
            overall_status = self._calculate_overall_status(all_checks)
            overall_risk_score = self._calculate_risk_score(all_checks)
            assessment = ComplianceAssessment(
                assessment_id=assessment_id,
                entity_id=entity_id,
                entity_type=entity_type,
                jurisdictions=jurisdictions,
                overall_status=overall_status,
                checks=all_checks,
                risk_score=overall_risk_score,
                timestamp=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            )
            self._compliance_cache[cache_key] = assessment
            self._active_assessments[assessment_id] = assessment
            await self.audit_service.log_compliance_event(
                event_type="compliance_assessment",
                entity_id=entity_id,
                entity_type=entity_type,
                details={
                    "assessment_id": assessment_id,
                    "jurisdictions": [j.value for j in jurisdictions],
                    "overall_status": overall_status.value,
                    "risk_score": overall_risk_score,
                },
            )
            self.logger.info(
                f"Compliance assessment completed for {entity_id}: {overall_status.value}"
            )
            return assessment
        except Exception as e:
            self.logger.error(
                f"Error in compliance assessment for {entity_id}: {str(e)}"
            )
            raise

    async def _assess_jurisdiction_compliance(
        self,
        entity_id: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        jurisdiction: Jurisdiction,
    ) -> List[ComplianceCheck]:
        """Assess compliance for a specific jurisdiction."""
        checks = []
        rules = self.regulatory_framework.get_applicable_rules(
            jurisdiction, entity_type
        )
        for rule in rules:
            try:
                check_result = await self._evaluate_compliance_rule(
                    rule, entity_id, entity_type, entity_data, jurisdiction
                )
                checks.append(check_result)
            except Exception as e:
                self.logger.error(f"Error evaluating rule {rule.rule_id}: {str(e)}")
                checks.append(
                    ComplianceCheck(
                        check_id=f"{rule.rule_id}_{entity_id}_{int(datetime.now(timezone.utc).timestamp())}",
                        rule_id=rule.rule_id,
                        jurisdiction=jurisdiction,
                        status=ComplianceStatus.UNKNOWN,
                        severity=ComplianceSeverity.MEDIUM,
                        description=f"Error evaluating rule: {str(e)}",
                        details={"error": str(e)},
                        timestamp=datetime.now(timezone.utc),
                    )
                )
        return checks

    async def _evaluate_compliance_rule(
        self,
        rule: ComplianceRule,
        entity_id: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        jurisdiction: Jurisdiction,
    ) -> ComplianceCheck:
        """Evaluate a specific compliance rule."""
        check_id = (
            f"{rule.rule_id}_{entity_id}_{int(datetime.now(timezone.utc).timestamp())}"
        )
        if rule.category == "aml":
            return await self._evaluate_aml_rule(
                rule, entity_id, entity_type, entity_data, check_id
            )
        elif rule.category == "kyc":
            return await self._evaluate_kyc_rule(
                rule, entity_id, entity_type, entity_data, check_id
            )
        elif rule.category == "data_protection":
            return await self._evaluate_data_protection_rule(
                rule, entity_id, entity_type, entity_data, check_id
            )
        elif rule.category == "transaction_monitoring":
            return await self._evaluate_transaction_monitoring_rule(
                rule, entity_id, entity_type, entity_data, check_id
            )
        elif rule.category == "reporting":
            return await self._evaluate_reporting_rule(
                rule, entity_id, entity_type, entity_data, check_id
            )
        else:
            return await self._evaluate_generic_rule(
                rule, entity_id, entity_type, entity_data, check_id
            )

    async def _evaluate_aml_rule(
        self,
        rule: ComplianceRule,
        entity_id: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        check_id: str,
    ) -> ComplianceCheck:
        """Evaluate AML-specific compliance rule."""
        if entity_type == "transaction":
            aml_result = await self.aml_engine.screen_transaction(entity_data)
        elif entity_type == "user":
            aml_result = await self.aml_engine.screen_customer(entity_data)
        else:
            aml_result = AMLResult(
                entity_id=entity_id,
                risk_score=0.0,
                status="unknown",
                flags=[],
                details={},
            )
        if aml_result.status == "clear":
            status = ComplianceStatus.COMPLIANT
            severity = ComplianceSeverity.LOW
        elif aml_result.status == "review":
            status = ComplianceStatus.PENDING_REVIEW
            severity = ComplianceSeverity.MEDIUM
        elif aml_result.status == "blocked":
            status = ComplianceStatus.NON_COMPLIANT
            severity = ComplianceSeverity.HIGH
        else:
            status = ComplianceStatus.UNKNOWN
            severity = ComplianceSeverity.MEDIUM
        return ComplianceCheck(
            check_id=check_id,
            rule_id=rule.rule_id,
            jurisdiction=rule.jurisdiction,
            status=status,
            severity=severity,
            description=f"AML screening: {aml_result.status}",
            details={
                "aml_result": aml_result.to_dict(),
                "risk_score": aml_result.risk_score,
                "flags": aml_result.flags,
            },
            timestamp=datetime.now(timezone.utc),
            remediation_required=status == ComplianceStatus.NON_COMPLIANT,
        )

    async def _evaluate_kyc_rule(
        self,
        rule: ComplianceRule,
        entity_id: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        check_id: str,
    ) -> ComplianceCheck:
        """Evaluate KYC-specific compliance rule."""
        if entity_type != "user":
            return ComplianceCheck(
                check_id=check_id,
                rule_id=rule.rule_id,
                jurisdiction=rule.jurisdiction,
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.LOW,
                description="KYC not applicable for this entity type",
                details={},
                timestamp=datetime.now(timezone.utc),
            )
        kyc_result = await self.kyc_service.verify_customer(entity_data)
        if kyc_result.status == "verified":
            status = ComplianceStatus.COMPLIANT
            severity = ComplianceSeverity.LOW
        elif kyc_result.status == "pending":
            status = ComplianceStatus.PENDING_REVIEW
            severity = ComplianceSeverity.MEDIUM
        elif kyc_result.status == "failed":
            status = ComplianceStatus.NON_COMPLIANT
            severity = ComplianceSeverity.HIGH
        else:
            status = ComplianceStatus.UNKNOWN
            severity = ComplianceSeverity.MEDIUM
        return ComplianceCheck(
            check_id=check_id,
            rule_id=rule.rule_id,
            jurisdiction=rule.jurisdiction,
            status=status,
            severity=severity,
            description=f"KYC verification: {kyc_result.status}",
            details={
                "kyc_result": kyc_result.to_dict(),
                "verification_level": kyc_result.verification_level,
                "documents_verified": kyc_result.documents_verified,
            },
            timestamp=datetime.now(timezone.utc),
            remediation_required=status == ComplianceStatus.NON_COMPLIANT,
        )

    async def _evaluate_data_protection_rule(
        self,
        rule: ComplianceRule,
        entity_id: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        check_id: str,
    ) -> ComplianceCheck:
        """Evaluate data protection compliance rule."""
        dp_result = await self.data_protection.assess_data_protection_compliance(
            entity_data, rule.jurisdiction
        )
        return ComplianceCheck(
            check_id=check_id,
            rule_id=rule.rule_id,
            jurisdiction=rule.jurisdiction,
            status=ComplianceStatus(dp_result["status"]),
            severity=ComplianceSeverity(dp_result["severity"]),
            description=dp_result["description"],
            details=dp_result["details"],
            timestamp=datetime.now(timezone.utc),
            remediation_required=dp_result.get("remediation_required", False),
        )

    async def _evaluate_transaction_monitoring_rule(
        self,
        rule: ComplianceRule,
        entity_id: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        check_id: str,
    ) -> ComplianceCheck:
        """Evaluate transaction monitoring compliance rule."""
        if entity_type != "transaction":
            return ComplianceCheck(
                check_id=check_id,
                rule_id=rule.rule_id,
                jurisdiction=rule.jurisdiction,
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.LOW,
                description="Transaction monitoring not applicable for this entity type",
                details={},
                timestamp=datetime.now(timezone.utc),
            )
        amount = entity_data.get("amount", 0)
        currency = entity_data.get("currency", "USD")
        country = entity_data.get("country_code", "US")
        violations = []
        if rule.jurisdiction == Jurisdiction.EU:
            if amount > 10000:
                violations.append("Large transaction requiring reporting")
            if country not in ["EU", "EEA"] and amount > 1000:
                violations.append("Cross-border transaction monitoring")
        elif rule.jurisdiction == Jurisdiction.US:
            if amount > 10000:
                violations.append("Currency Transaction Report required")
            if amount >= 3000:
                violations.append("Suspicious Activity Report monitoring")
        elif rule.jurisdiction == Jurisdiction.SINGAPORE:
            if amount > 20000:
                violations.append("Large transaction monitoring")
        if violations:
            status = ComplianceStatus.REQUIRES_ACTION
            severity = ComplianceSeverity.MEDIUM
            description = f"Transaction monitoring violations: {', '.join(violations)}"
        else:
            status = ComplianceStatus.COMPLIANT
            severity = ComplianceSeverity.LOW
            description = "Transaction monitoring compliance verified"
        return ComplianceCheck(
            check_id=check_id,
            rule_id=rule.rule_id,
            jurisdiction=rule.jurisdiction,
            status=status,
            severity=severity,
            description=description,
            details={
                "violations": violations,
                "amount": amount,
                "currency": currency,
                "country": country,
            },
            timestamp=datetime.now(timezone.utc),
            remediation_required=len(violations) > 0,
        )

    async def _evaluate_reporting_rule(
        self,
        rule: ComplianceRule,
        entity_id: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        check_id: str,
    ) -> ComplianceCheck:
        """Evaluate regulatory reporting compliance rule."""
        reporting_result = await self.reporting_service.check_reporting_requirements(
            entity_data, rule.jurisdiction
        )
        return ComplianceCheck(
            check_id=check_id,
            rule_id=rule.rule_id,
            jurisdiction=rule.jurisdiction,
            status=ComplianceStatus(reporting_result["status"]),
            severity=ComplianceSeverity(reporting_result["severity"]),
            description=reporting_result["description"],
            details=reporting_result["details"],
            timestamp=datetime.now(timezone.utc),
            remediation_required=reporting_result.get("remediation_required", False),
        )

    async def _evaluate_generic_rule(
        self,
        rule: ComplianceRule,
        entity_id: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        check_id: str,
    ) -> ComplianceCheck:
        """Evaluate generic compliance rule."""
        return ComplianceCheck(
            check_id=check_id,
            rule_id=rule.rule_id,
            jurisdiction=rule.jurisdiction,
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.LOW,
            description=f"Generic rule {rule.rule_id} evaluated",
            details={"rule_type": "generic"},
            timestamp=datetime.now(timezone.utc),
        )

    def _calculate_overall_status(
        self, checks: List[ComplianceCheck]
    ) -> ComplianceStatus:
        """Calculate overall compliance status from individual checks."""
        if not checks:
            return ComplianceStatus.UNKNOWN
        statuses = [check.status for check in checks]
        if ComplianceStatus.NON_COMPLIANT in statuses:
            return ComplianceStatus.NON_COMPLIANT
        elif ComplianceStatus.REQUIRES_ACTION in statuses:
            return ComplianceStatus.REQUIRES_ACTION
        elif ComplianceStatus.PENDING_REVIEW in statuses:
            return ComplianceStatus.PENDING_REVIEW
        elif all((status == ComplianceStatus.COMPLIANT for status in statuses)):
            return ComplianceStatus.COMPLIANT
        else:
            return ComplianceStatus.UNKNOWN

    def _calculate_risk_score(self, checks: List[ComplianceCheck]) -> float:
        """Calculate overall risk score from individual checks."""
        if not checks:
            return 0.0
        severity_weights = {
            ComplianceSeverity.LOW: 0.1,
            ComplianceSeverity.MEDIUM: 0.3,
            ComplianceSeverity.HIGH: 0.7,
            ComplianceSeverity.CRITICAL: 1.0,
        }
        status_scores = {
            ComplianceStatus.COMPLIANT: 0.0,
            ComplianceStatus.PENDING_REVIEW: 0.3,
            ComplianceStatus.REQUIRES_ACTION: 0.6,
            ComplianceStatus.NON_COMPLIANT: 1.0,
            ComplianceStatus.UNKNOWN: 0.5,
        }
        total_score = 0.0
        total_weight = 0.0
        for check in checks:
            weight = severity_weights.get(check.severity, 0.5)
            score = status_scores.get(check.status, 0.5)
            total_score += score * weight
            total_weight += weight
        return total_score / total_weight if total_weight > 0 else 0.0

    async def _get_entity_data(
        self, entity_id: str, entity_type: str
    ) -> Dict[str, Any]:
        """Retrieve entity data for compliance assessment."""
        if entity_type == "user":
            return {
                "user_id": entity_id,
                "email": f"user_{entity_id}@example.com",
                "country_code": "US",
                "kyc_status": "pending",
                "account_created": datetime.now(timezone.utc).isoformat(),
                "last_login": datetime.now(timezone.utc).isoformat(),
            }
        elif entity_type == "transaction":
            return {
                "transaction_id": entity_id,
                "amount": 1000.0,
                "currency": "USD",
                "country_code": "US",
                "payment_method": "card",
                "merchant_category": "retail",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return {"entity_id": entity_id, "entity_type": entity_type}

    async def monitor_compliance(
        self, entity_id: str, entity_type: str, jurisdictions: List[Jurisdiction] = None
    ) -> Dict[str, Any]:
        """Start continuous compliance monitoring for an entity."""
        if not self._monitoring_enabled:
            return {"status": "monitoring_disabled"}
        assessment = await self.assess_compliance(entity_id, entity_type, jurisdictions)
        if assessment.risk_score > 0.7:
            monitoring_interval = timedelta(hours=1)
        elif assessment.risk_score > 0.4:
            monitoring_interval = timedelta(hours=6)
        else:
            monitoring_interval = timedelta(days=1)
        monitoring_config = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "jurisdictions": jurisdictions,
            "interval": monitoring_interval,
            "last_check": datetime.now(timezone.utc),
            "next_check": datetime.now(timezone.utc) + monitoring_interval,
        }
        return {
            "status": "monitoring_started",
            "assessment": assessment.to_dict(),
            "monitoring_config": monitoring_config,
        }

    async def get_compliance_status(
        self, entity_id: str, entity_type: str
    ) -> Dict[str, Any]:
        """Get current compliance status for an entity."""
        f"{entity_type}_{entity_id}"
        for assessment in self._active_assessments.values():
            if (
                assessment.entity_id == entity_id
                and assessment.entity_type == entity_type
            ):
                return assessment.to_dict()
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "status": "no_assessment_found",
            "message": "No compliance assessment found. Please run assessment first.",
        }

    async def remediate_compliance_issue(
        self,
        check_id: str,
        remediation_action: str,
        remediation_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Initiate remediation for a compliance issue."""
        target_check = None
        target_assessment = None
        for assessment in self._active_assessments.values():
            for check in assessment.checks:
                if check.check_id == check_id:
                    target_check = check
                    target_assessment = assessment
                    break
            if target_check:
                break
        if not target_check:
            return {
                "status": "error",
                "message": f"Compliance check {check_id} not found",
            }
        await self.audit_service.log_compliance_event(
            event_type="remediation_initiated",
            entity_id=target_assessment.entity_id,
            entity_type=target_assessment.entity_type,
            details={
                "check_id": check_id,
                "remediation_action": remediation_action,
                "remediation_data": remediation_data or {},
            },
        )
        if remediation_action == "manual_review":
            target_check.status = ComplianceStatus.PENDING_REVIEW
        elif remediation_action == "auto_approve":
            target_check.status = ComplianceStatus.COMPLIANT
        elif remediation_action == "request_documents":
            target_check.status = ComplianceStatus.PENDING_REVIEW
            target_check.remediation_deadline = datetime.now(timezone.utc) + timedelta(
                days=7
            )
        target_assessment.overall_status = self._calculate_overall_status(
            target_assessment.checks
        )
        target_assessment.risk_score = self._calculate_risk_score(
            target_assessment.checks
        )
        return {
            "status": "remediation_initiated",
            "check_id": check_id,
            "new_status": target_check.status.value,
            "assessment_updated": True,
        }

    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance metrics and statistics."""
        total_assessments = len(self._active_assessments)
        if total_assessments == 0:
            return {
                "total_assessments": 0,
                "compliance_rate": 0.0,
                "average_risk_score": 0.0,
                "status_distribution": {},
            }
        compliant_count = sum(
            (
                1
                for a in self._active_assessments.values()
                if a.overall_status == ComplianceStatus.COMPLIANT
            )
        )
        compliance_rate = compliant_count / total_assessments
        average_risk_score = (
            sum((a.risk_score for a in self._active_assessments.values()))
            / total_assessments
        )
        status_counts = {}
        for assessment in self._active_assessments.values():
            status = assessment.overall_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        return {
            "total_assessments": total_assessments,
            "compliance_rate": compliance_rate,
            "average_risk_score": average_risk_score,
            "status_distribution": status_counts,
            "monitoring_enabled": self._monitoring_enabled,
        }

    def enable_monitoring(self) -> object:
        """Enable compliance monitoring."""
        self._monitoring_enabled = True
        self.logger.info("Compliance monitoring enabled")

    def disable_monitoring(self) -> object:
        """Disable compliance monitoring."""
        self._monitoring_enabled = False
        self.logger.info("Compliance monitoring disabled")

    async def generate_compliance_report(
        self,
        jurisdiction: Jurisdiction = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        return await self.reporting_service.generate_compliance_report(
            jurisdiction=jurisdiction,
            start_date=start_date,
            end_date=end_date,
            assessments=list(self._active_assessments.values()),
        )
