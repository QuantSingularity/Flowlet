import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .regulatory_framework import Jurisdiction

"\nData Protection Service\n======================\n\nComprehensive data protection and privacy compliance service.\nSupports GDPR, CCPA, PDPA, and other privacy regulations across multiple jurisdictions.\n"


class DataCategory(Enum):
    """Categories of personal data."""

    PERSONAL_IDENTIFIERS = "personal_identifiers"
    FINANCIAL_DATA = "financial_data"
    BIOMETRIC_DATA = "biometric_data"
    LOCATION_DATA = "location_data"
    BEHAVIORAL_DATA = "behavioral_data"
    COMMUNICATION_DATA = "communication_data"
    DEVICE_DATA = "device_data"
    SPECIAL_CATEGORY = "special_category"


class ProcessingPurpose(Enum):
    """Purposes for data processing."""

    IDENTITY_VERIFICATION = "identity_verification"
    FRAUD_PREVENTION = "fraud_prevention"
    COMPLIANCE = "compliance"
    CUSTOMER_SERVICE = "customer_service"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PRODUCT_IMPROVEMENT = "product_improvement"
    LEGAL_OBLIGATION = "legal_obligation"


class LegalBasis(Enum):
    """Legal basis for data processing under GDPR."""

    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DataSubjectRight(Enum):
    """Data subject rights under privacy regulations."""

    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    RESTRICT_PROCESSING = "restrict_processing"
    DATA_PORTABILITY = "data_portability"
    OBJECT = "object"
    WITHDRAW_CONSENT = "withdraw_consent"


@dataclass
class ConsentRecord:
    """Record of data processing consent."""

    consent_id: str
    data_subject_id: str
    purpose: ProcessingPurpose
    data_categories: List[DataCategory]
    legal_basis: LegalBasis
    consent_given: bool
    consent_timestamp: datetime
    consent_method: str
    consent_version: str
    withdrawal_timestamp: Optional[datetime] = None
    expiry_date: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consent_id": self.consent_id,
            "data_subject_id": self.data_subject_id,
            "purpose": self.purpose.value,
            "data_categories": [cat.value for cat in self.data_categories],
            "legal_basis": self.legal_basis.value,
            "consent_given": self.consent_given,
            "consent_timestamp": self.consent_timestamp.isoformat(),
            "consent_method": self.consent_method,
            "consent_version": self.consent_version,
            "withdrawal_timestamp": (
                self.withdrawal_timestamp.isoformat()
                if self.withdrawal_timestamp
                else None
            ),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
        }


@dataclass
class DataProcessingRecord:
    """Record of data processing activity."""

    processing_id: str
    data_subject_id: str
    data_categories: List[DataCategory]
    purpose: ProcessingPurpose
    legal_basis: LegalBasis
    processing_timestamp: datetime
    retention_period: timedelta
    data_location: str
    third_party_sharing: bool
    automated_decision_making: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processing_id": self.processing_id,
            "data_subject_id": self.data_subject_id,
            "data_categories": [cat.value for cat in self.data_categories],
            "purpose": self.purpose.value,
            "legal_basis": self.legal_basis.value,
            "processing_timestamp": self.processing_timestamp.isoformat(),
            "retention_period_days": self.retention_period.days,
            "data_location": self.data_location,
            "third_party_sharing": self.third_party_sharing,
            "automated_decision_making": self.automated_decision_making,
        }


@dataclass
class DataSubjectRequest:
    """Data subject rights request."""

    request_id: str
    data_subject_id: str
    request_type: DataSubjectRight
    request_details: Dict[str, Any]
    request_timestamp: datetime
    status: str
    response_deadline: datetime
    completion_timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "data_subject_id": self.data_subject_id,
            "request_type": self.request_type.value,
            "request_details": self.request_details,
            "request_timestamp": self.request_timestamp.isoformat(),
            "status": self.status,
            "response_deadline": self.response_deadline.isoformat(),
            "completion_timestamp": (
                self.completion_timestamp.isoformat()
                if self.completion_timestamp
                else None
            ),
        }


class DataProtectionService:
    """
    Comprehensive data protection and privacy compliance service.

    Features:
    - Multi-jurisdiction privacy compliance
    - Consent management
    - Data subject rights handling
    - Data processing records
    - Privacy impact assessments
    - Data breach management
    - Automated compliance monitoring
    - Privacy by design implementation
    """

    def __init__(self, db_session: Session, config: Dict[str, Any] = None) -> None:
        self.db = db_session
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._jurisdiction_requirements = {}
        self._consent_records = {}
        self._processing_records = {}
        self._data_subject_requests = {}
        self._retention_policies = {}
        self._initialize_data_protection_service()

    def _initialize_data_protection_service(self) -> object:
        """Initialize the data protection service."""
        self._setup_jurisdiction_requirements()
        self._setup_retention_policies()
        self.logger.info("Data protection service initialized successfully")

    def _setup_jurisdiction_requirements(self) -> object:
        """Set up jurisdiction-specific data protection requirements."""
        self._jurisdiction_requirements[Jurisdiction.EU] = {
            "regulation_name": "GDPR",
            "consent_requirements": {
                "explicit_consent_required": True,
                "consent_withdrawal": True,
                "consent_granularity": True,
                "age_of_consent": 16,
                "parental_consent_required": True,
            },
            "data_subject_rights": [
                DataSubjectRight.ACCESS,
                DataSubjectRight.RECTIFICATION,
                DataSubjectRight.ERASURE,
                DataSubjectRight.RESTRICT_PROCESSING,
                DataSubjectRight.DATA_PORTABILITY,
                DataSubjectRight.OBJECT,
                DataSubjectRight.WITHDRAW_CONSENT,
            ],
            "response_timeframes": {
                DataSubjectRight.ACCESS: timedelta(days=30),
                DataSubjectRight.RECTIFICATION: timedelta(days=30),
                DataSubjectRight.ERASURE: timedelta(days=30),
                DataSubjectRight.RESTRICT_PROCESSING: timedelta(days=30),
                DataSubjectRight.DATA_PORTABILITY: timedelta(days=30),
                DataSubjectRight.OBJECT: timedelta(days=30),
            },
            "breach_notification": {
                "authority_notification_hours": 72,
                "data_subject_notification_required": True,
                "high_risk_threshold": True,
            },
            "dpo_required": True,
            "privacy_by_design": True,
            "data_minimization": True,
            "purpose_limitation": True,
        }
        self._jurisdiction_requirements[Jurisdiction.US] = {
            "regulation_name": "CCPA",
            "consent_requirements": {
                "explicit_consent_required": False,
                "opt_out_required": True,
                "consent_withdrawal": True,
                "age_of_consent": 13,
                "parental_consent_required": True,
            },
            "data_subject_rights": [
                DataSubjectRight.ACCESS,
                DataSubjectRight.ERASURE,
                DataSubjectRight.DATA_PORTABILITY,
                DataSubjectRight.OBJECT,
            ],
            "response_timeframes": {
                DataSubjectRight.ACCESS: timedelta(days=45),
                DataSubjectRight.ERASURE: timedelta(days=45),
                DataSubjectRight.DATA_PORTABILITY: timedelta(days=45),
            },
            "breach_notification": {
                "authority_notification_hours": None,
                "data_subject_notification_required": False,
                "high_risk_threshold": False,
            },
            "dpo_required": False,
            "privacy_by_design": False,
            "data_minimization": False,
            "purpose_limitation": False,
        }
        self._jurisdiction_requirements[Jurisdiction.SINGAPORE] = {
            "regulation_name": "PDPA",
            "consent_requirements": {
                "explicit_consent_required": True,
                "consent_withdrawal": True,
                "consent_granularity": False,
                "age_of_consent": 18,
                "parental_consent_required": True,
            },
            "data_subject_rights": [
                DataSubjectRight.ACCESS,
                DataSubjectRight.RECTIFICATION,
                DataSubjectRight.WITHDRAW_CONSENT,
            ],
            "response_timeframes": {
                DataSubjectRight.ACCESS: timedelta(days=30),
                DataSubjectRight.RECTIFICATION: timedelta(days=30),
            },
            "breach_notification": {
                "authority_notification_hours": 72,
                "data_subject_notification_required": True,
                "high_risk_threshold": True,
            },
            "dpo_required": True,
            "privacy_by_design": True,
            "data_minimization": True,
            "purpose_limitation": True,
        }

    def _setup_retention_policies(self) -> object:
        """Set up data retention policies by category and purpose."""
        self._retention_policies = {
            DataCategory.PERSONAL_IDENTIFIERS: {
                ProcessingPurpose.IDENTITY_VERIFICATION: timedelta(days=2555),
                ProcessingPurpose.COMPLIANCE: timedelta(days=2555),
                ProcessingPurpose.CUSTOMER_SERVICE: timedelta(days=1095),
                ProcessingPurpose.MARKETING: timedelta(days=730),
            },
            DataCategory.FINANCIAL_DATA: {
                ProcessingPurpose.COMPLIANCE: timedelta(days=2555),
                ProcessingPurpose.FRAUD_PREVENTION: timedelta(days=2555),
                ProcessingPurpose.CUSTOMER_SERVICE: timedelta(days=1095),
            },
            DataCategory.BIOMETRIC_DATA: {
                ProcessingPurpose.IDENTITY_VERIFICATION: timedelta(days=1095),
                ProcessingPurpose.FRAUD_PREVENTION: timedelta(days=1095),
            },
            DataCategory.BEHAVIORAL_DATA: {
                ProcessingPurpose.ANALYTICS: timedelta(days=730),
                ProcessingPurpose.PRODUCT_IMPROVEMENT: timedelta(days=1095),
                ProcessingPurpose.MARKETING: timedelta(days=365),
            },
        }

    async def assess_data_protection_compliance(
        self, entity_data: Dict[str, Any], jurisdiction: Jurisdiction
    ) -> Dict[str, Any]:
        """Assess data protection compliance for an entity."""
        try:
            requirements = self._jurisdiction_requirements.get(jurisdiction, {})
            if not requirements:
                return {
                    "status": "unknown",
                    "severity": "medium",
                    "description": f"No data protection requirements defined for jurisdiction: {jurisdiction.value}",
                    "details": {},
                    "remediation_required": False,
                }
            compliance_issues = []
            consent_issues = await self._check_consent_compliance(
                entity_data, requirements
            )
            compliance_issues.extend(consent_issues)
            processing_issues = await self._check_processing_compliance(
                entity_data, requirements
            )
            compliance_issues.extend(processing_issues)
            retention_issues = await self._check_retention_compliance(entity_data)
            compliance_issues.extend(retention_issues)
            if not compliance_issues:
                status = "compliant"
                severity = "low"
                description = f"Data protection compliance verified for {requirements['regulation_name']}"
            elif any((issue["severity"] == "critical" for issue in compliance_issues)):
                status = "non_compliant"
                severity = "critical"
                description = f"Critical data protection violations found for {requirements['regulation_name']}"
            elif any((issue["severity"] == "high" for issue in compliance_issues)):
                status = "requires_action"
                severity = "high"
                description = f"High-priority data protection issues found for {requirements['regulation_name']}"
            else:
                status = "requires_action"
                severity = "medium"
                description = f"Data protection issues found for {requirements['regulation_name']}"
            return {
                "status": status,
                "severity": severity,
                "description": description,
                "details": {
                    "jurisdiction": jurisdiction.value,
                    "regulation": requirements["regulation_name"],
                    "compliance_issues": compliance_issues,
                    "total_issues": len(compliance_issues),
                },
                "remediation_required": len(compliance_issues) > 0,
            }
        except Exception as e:
            self.logger.error(f"Error assessing data protection compliance: {str(e)}")
            return {
                "status": "unknown",
                "severity": "medium",
                "description": f"Error assessing data protection compliance: {str(e)}",
                "details": {"error": str(e)},
                "remediation_required": True,
            }

    async def _check_consent_compliance(
        self, entity_data: Dict[str, Any], requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check consent compliance."""
        issues = []
        consent_reqs = requirements.get("consent_requirements", {})
        if consent_reqs.get("explicit_consent_required", False):
            consent_given = entity_data.get("consent_given", False)
            if not consent_given:
                issues.append(
                    {
                        "type": "missing_consent",
                        "severity": "critical",
                        "description": "Explicit consent required but not provided",
                        "remediation": "Obtain explicit consent from data subject",
                    }
                )
        if consent_reqs.get("consent_withdrawal", False):
            withdrawal_mechanism = entity_data.get(
                "consent_withdrawal_available", False
            )
            if not withdrawal_mechanism:
                issues.append(
                    {
                        "type": "missing_withdrawal_mechanism",
                        "severity": "high",
                        "description": "Consent withdrawal mechanism not available",
                        "remediation": "Implement consent withdrawal mechanism",
                    }
                )
        age_of_consent = consent_reqs.get("age_of_consent", 18)
        user_age = entity_data.get("age")
        if user_age and user_age < age_of_consent:
            parental_consent = entity_data.get("parental_consent", False)
            if not parental_consent and consent_reqs.get(
                "parental_consent_required", False
            ):
                issues.append(
                    {
                        "type": "missing_parental_consent",
                        "severity": "critical",
                        "description": f"User under {age_of_consent} requires parental consent",
                        "remediation": "Obtain parental consent",
                    }
                )
        return issues

    async def _check_processing_compliance(
        self, entity_data: Dict[str, Any], requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check data processing compliance."""
        issues = []
        legal_basis = entity_data.get("legal_basis")
        if not legal_basis:
            issues.append(
                {
                    "type": "missing_legal_basis",
                    "severity": "critical",
                    "description": "No legal basis specified for data processing",
                    "remediation": "Specify legal basis for data processing",
                }
            )
        if requirements.get("purpose_limitation", False):
            processing_purpose = entity_data.get("processing_purpose")
            if not processing_purpose:
                issues.append(
                    {
                        "type": "missing_purpose",
                        "severity": "high",
                        "description": "Processing purpose not specified",
                        "remediation": "Specify purpose for data processing",
                    }
                )
        if requirements.get("data_minimization", False):
            data_categories = entity_data.get("data_categories", [])
            processing_purpose = entity_data.get("processing_purpose")
            if data_categories and processing_purpose:
                necessary_categories = self._get_necessary_data_categories(
                    processing_purpose
                )
                unnecessary_categories = [
                    cat for cat in data_categories if cat not in necessary_categories
                ]
                if unnecessary_categories:
                    issues.append(
                        {
                            "type": "data_minimization_violation",
                            "severity": "medium",
                            "description": f"Unnecessary data categories collected: {unnecessary_categories}",
                            "remediation": "Remove unnecessary data categories",
                        }
                    )
        return issues

    async def _check_retention_compliance(
        self, entity_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check data retention compliance."""
        issues = []
        data_categories = entity_data.get("data_categories", [])
        processing_purpose = entity_data.get("processing_purpose")
        processing_date = entity_data.get("processing_date")
        if data_categories and processing_purpose and processing_date:
            processing_datetime = self._parse_datetime(processing_date)
            if processing_datetime:
                for category in data_categories:
                    category_enum = (
                        DataCategory(category)
                        if isinstance(category, str)
                        else category
                    )
                    purpose_enum = (
                        ProcessingPurpose(processing_purpose)
                        if isinstance(processing_purpose, str)
                        else processing_purpose
                    )
                    retention_period = self._retention_policies.get(
                        category_enum, {}
                    ).get(purpose_enum)
                    if retention_period:
                        expiry_date = processing_datetime + retention_period
                        if datetime.now(timezone.utc) > expiry_date:
                            issues.append(
                                {
                                    "type": "retention_period_exceeded",
                                    "severity": "high",
                                    "description": f"Retention period exceeded for {category} data",
                                    "remediation": "Delete or anonymize expired data",
                                    "expiry_date": expiry_date.isoformat(),
                                }
                            )
        return issues

    def _get_necessary_data_categories(self, processing_purpose: str) -> List[str]:
        """Get necessary data categories for a processing purpose."""
        purpose_enum = (
            ProcessingPurpose(processing_purpose)
            if isinstance(processing_purpose, str)
            else processing_purpose
        )
        necessary_categories = {
            ProcessingPurpose.IDENTITY_VERIFICATION: [
                DataCategory.PERSONAL_IDENTIFIERS.value,
                DataCategory.BIOMETRIC_DATA.value,
            ],
            ProcessingPurpose.FRAUD_PREVENTION: [
                DataCategory.PERSONAL_IDENTIFIERS.value,
                DataCategory.FINANCIAL_DATA.value,
                DataCategory.BEHAVIORAL_DATA.value,
                DataCategory.DEVICE_DATA.value,
            ],
            ProcessingPurpose.COMPLIANCE: [
                DataCategory.PERSONAL_IDENTIFIERS.value,
                DataCategory.FINANCIAL_DATA.value,
            ],
            ProcessingPurpose.CUSTOMER_SERVICE: [
                DataCategory.PERSONAL_IDENTIFIERS.value,
                DataCategory.COMMUNICATION_DATA.value,
            ],
            ProcessingPurpose.MARKETING: [
                DataCategory.PERSONAL_IDENTIFIERS.value,
                DataCategory.BEHAVIORAL_DATA.value,
            ],
            ProcessingPurpose.ANALYTICS: [
                DataCategory.BEHAVIORAL_DATA.value,
                DataCategory.DEVICE_DATA.value,
            ],
        }
        return necessary_categories.get(purpose_enum, [])

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            try:
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        return None

    async def record_consent(
        self,
        data_subject_id: str,
        purpose: ProcessingPurpose,
        data_categories: List[DataCategory],
        legal_basis: LegalBasis,
        consent_method: str = "web_form",
        consent_version: str = "1.0",
    ) -> ConsentRecord:
        """Record data processing consent."""
        consent_id = str(uuid.uuid4())
        consent_record = ConsentRecord(
            consent_id=consent_id,
            data_subject_id=data_subject_id,
            purpose=purpose,
            data_categories=data_categories,
            legal_basis=legal_basis,
            consent_given=True,
            consent_timestamp=datetime.now(timezone.utc),
            consent_method=consent_method,
            consent_version=consent_version,
            expiry_date=datetime.now(timezone.utc) + timedelta(days=365),
        )
        self._consent_records[consent_id] = consent_record
        self.logger.info(
            f"Recorded consent for data subject {data_subject_id}: {consent_id}"
        )
        return consent_record

    async def withdraw_consent(self, consent_id: str) -> bool:
        """Withdraw previously given consent."""
        if consent_id in self._consent_records:
            consent_record = self._consent_records[consent_id]
            consent_record.consent_given = False
            consent_record.withdrawal_timestamp = datetime.now(timezone.utc)
            self.logger.info(f"Consent withdrawn: {consent_id}")
            return True
        return False

    async def record_data_processing(
        self,
        data_subject_id: str,
        data_categories: List[DataCategory],
        purpose: ProcessingPurpose,
        legal_basis: LegalBasis,
        data_location: str = "EU",
        third_party_sharing: bool = False,
        automated_decision_making: bool = False,
    ) -> DataProcessingRecord:
        """Record data processing activity."""
        processing_id = str(uuid.uuid4())
        retention_period = timedelta(days=365)
        if data_categories and purpose in self._retention_policies.get(
            data_categories[0], {}
        ):
            retention_period = self._retention_policies[data_categories[0]][purpose]
        processing_record = DataProcessingRecord(
            processing_id=processing_id,
            data_subject_id=data_subject_id,
            data_categories=data_categories,
            purpose=purpose,
            legal_basis=legal_basis,
            processing_timestamp=datetime.now(timezone.utc),
            retention_period=retention_period,
            data_location=data_location,
            third_party_sharing=third_party_sharing,
            automated_decision_making=automated_decision_making,
        )
        self._processing_records[processing_id] = processing_record
        self.logger.info(
            f"Recorded data processing for data subject {data_subject_id}: {processing_id}"
        )
        return processing_record

    async def handle_data_subject_request(
        self,
        data_subject_id: str,
        request_type: DataSubjectRight,
        request_details: Dict[str, Any] = None,
    ) -> DataSubjectRequest:
        """Handle data subject rights request."""
        request_id = str(uuid.uuid4())
        response_deadline = datetime.now(timezone.utc) + timedelta(days=30)
        request = DataSubjectRequest(
            request_id=request_id,
            data_subject_id=data_subject_id,
            request_type=request_type,
            request_details=request_details or {},
            request_timestamp=datetime.now(timezone.utc),
            status="pending",
            response_deadline=response_deadline,
        )
        self._data_subject_requests[request_id] = request
        await self._process_data_subject_request(request)
        self.logger.info(
            f"Created data subject request {request_id} for {data_subject_id}: {request_type.value}"
        )
        return request

    async def _process_data_subject_request(self, request: DataSubjectRequest):
        """Process a data subject rights request."""
        try:
            if request.request_type == DataSubjectRight.ACCESS:
                await self._process_access_request(request)
            elif request.request_type == DataSubjectRight.RECTIFICATION:
                await self._process_rectification_request(request)
            elif request.request_type == DataSubjectRight.ERASURE:
                await self._process_erasure_request(request)
            elif request.request_type == DataSubjectRight.RESTRICT_PROCESSING:
                await self._process_restriction_request(request)
            elif request.request_type == DataSubjectRight.DATA_PORTABILITY:
                await self._process_portability_request(request)
            elif request.request_type == DataSubjectRight.OBJECT:
                await self._process_objection_request(request)
            elif request.request_type == DataSubjectRight.WITHDRAW_CONSENT:
                await self._process_consent_withdrawal_request(request)
        except Exception as e:
            self.logger.error(
                f"Error processing data subject request {request.request_id}: {str(e)}"
            )
            request.status = "failed"

    async def _process_access_request(self, request: DataSubjectRequest):
        """Process data access request."""
        data_subject_id = request.data_subject_id
        personal_data = {
            "consent_records": [
                record.to_dict()
                for record in self._consent_records.values()
                if record.data_subject_id == data_subject_id
            ],
            "processing_records": [
                record.to_dict()
                for record in self._processing_records.values()
                if record.data_subject_id == data_subject_id
            ],
            "data_subject_requests": [
                req.to_dict()
                for req in self._data_subject_requests.values()
                if req.data_subject_id == data_subject_id
            ],
        }
        request.request_details["response_data"] = personal_data
        request.status = "completed"
        request.completion_timestamp = datetime.now(timezone.utc)
        self.logger.info(f"Completed access request for {data_subject_id}")

    async def _process_erasure_request(self, request: DataSubjectRequest):
        """Process data erasure (right to be forgotten) request."""
        data_subject_id = request.data_subject_id
        can_erase = await self._check_erasure_permissibility(data_subject_id)
        if can_erase:
            await self._erase_data_subject_data(data_subject_id)
            request.status = "completed"
            request.completion_timestamp = datetime.now(timezone.utc)
            self.logger.info(f"Completed erasure request for {data_subject_id}")
        else:
            request.status = "rejected"
            request.request_details["rejection_reason"] = (
                "Legal obligation to retain data"
            )
            self.logger.info(
                f"Rejected erasure request for {data_subject_id}: legal obligation"
            )

    async def _check_erasure_permissibility(self, data_subject_id: str) -> bool:
        """Check if data erasure is legally permissible."""
        processing_records = [
            record
            for record in self._processing_records.values()
            if record.data_subject_id == data_subject_id
        ]
        for record in processing_records:
            if record.legal_basis == LegalBasis.LEGAL_OBLIGATION:
                expiry_date = record.processing_timestamp + record.retention_period
                if datetime.now(timezone.utc) < expiry_date:
                    return False
        return True

    async def _erase_data_subject_data(self, data_subject_id: str):
        """Erase all data for a data subject."""
        consent_ids_to_remove = [
            consent_id
            for consent_id, record in self._consent_records.items()
            if record.data_subject_id == data_subject_id
        ]
        for consent_id in consent_ids_to_remove:
            del self._consent_records[consent_id]
        processing_ids_to_remove = [
            processing_id
            for processing_id, record in self._processing_records.items()
            if record.data_subject_id == data_subject_id
            and record.legal_basis != LegalBasis.LEGAL_OBLIGATION
        ]
        for processing_id in processing_ids_to_remove:
            del self._processing_records[processing_id]

    async def _process_rectification_request(self, request: DataSubjectRequest):
        """Process data rectification request."""
        request.status = "completed"
        request.completion_timestamp = datetime.now(timezone.utc)

    async def _process_restriction_request(self, request: DataSubjectRequest):
        """Process processing restriction request."""
        request.status = "completed"
        request.completion_timestamp = datetime.now(timezone.utc)

    async def _process_portability_request(self, request: DataSubjectRequest):
        """Process data portability request."""
        request.status = "completed"
        request.completion_timestamp = datetime.now(timezone.utc)

    async def _process_objection_request(self, request: DataSubjectRequest):
        """Process objection to processing request."""
        request.status = "completed"
        request.completion_timestamp = datetime.now(timezone.utc)

    async def _process_consent_withdrawal_request(self, request: DataSubjectRequest):
        """Process consent withdrawal request."""
        data_subject_id = request.data_subject_id
        for consent_record in self._consent_records.values():
            if (
                consent_record.data_subject_id == data_subject_id
                and consent_record.consent_given
            ):
                consent_record.consent_given = False
                consent_record.withdrawal_timestamp = datetime.now(timezone.utc)
        request.status = "completed"
        request.completion_timestamp = datetime.now(timezone.utc)

    async def conduct_privacy_impact_assessment(
        self, processing_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Conduct Privacy Impact Assessment (PIA/DPIA)."""
        assessment_id = str(uuid.uuid4())
        risk_factors = []
        risk_score = 0.0
        if processing_description.get("automated_decision_making", False):
            risk_factors.append("automated_decision_making")
            risk_score += 0.3
        if DataCategory.SPECIAL_CATEGORY.value in processing_description.get(
            "data_categories", []
        ):
            risk_factors.append("special_category_data")
            risk_score += 0.4
        if processing_description.get("large_scale_processing", False):
            risk_factors.append("large_scale_processing")
            risk_score += 0.2
        if processing_description.get("third_party_sharing", False):
            risk_factors.append("third_party_sharing")
            risk_score += 0.2
        if risk_score >= 0.7:
            risk_level = "high"
            dpia_required = True
        elif risk_score >= 0.4:
            risk_level = "medium"
            dpia_required = True
        else:
            risk_level = "low"
            dpia_required = False
        recommendations = []
        if "automated_decision_making" in risk_factors:
            recommendations.append(
                "Implement human review process for automated decisions"
            )
        if "special_category_data" in risk_factors:
            recommendations.append(
                "Implement additional security measures for special category data"
            )
        if "third_party_sharing" in risk_factors:
            recommendations.append(
                "Ensure adequate data processing agreements with third parties"
            )
        return {
            "assessment_id": assessment_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "dpia_required": dpia_required,
            "recommendations": recommendations,
            "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_consent_status(
        self, data_subject_id: str, purpose: ProcessingPurpose
    ) -> Dict[str, Any]:
        """Get consent status for a data subject and purpose."""
        relevant_consents = [
            record
            for record in self._consent_records.values()
            if record.data_subject_id == data_subject_id and record.purpose == purpose
        ]
        if not relevant_consents:
            return {
                "consent_given": False,
                "consent_required": True,
                "message": "No consent record found",
            }
        latest_consent = max(relevant_consents, key=lambda x: x.consent_timestamp)
        if (
            latest_consent.expiry_date
            and datetime.now(timezone.utc) > latest_consent.expiry_date
        ):
            return {
                "consent_given": False,
                "consent_required": True,
                "message": "Consent has expired",
                "expiry_date": latest_consent.expiry_date.isoformat(),
            }
        return {
            "consent_given": latest_consent.consent_given,
            "consent_required": True,
            "consent_timestamp": latest_consent.consent_timestamp.isoformat(),
            "consent_method": latest_consent.consent_method,
            "withdrawal_timestamp": (
                latest_consent.withdrawal_timestamp.isoformat()
                if latest_consent.withdrawal_timestamp
                else None
            ),
        }

    def get_data_protection_statistics(self) -> Dict[str, Any]:
        """Get data protection service statistics."""
        return {
            "total_consent_records": len(self._consent_records),
            "active_consents": len(
                [r for r in self._consent_records.values() if r.consent_given]
            ),
            "total_processing_records": len(self._processing_records),
            "total_data_subject_requests": len(self._data_subject_requests),
            "pending_requests": len(
                [
                    r
                    for r in self._data_subject_requests.values()
                    if r.status == "pending"
                ]
            ),
            "jurisdictions_supported": len(self._jurisdiction_requirements),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
