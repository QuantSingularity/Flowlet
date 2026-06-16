from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

"\nRegulatory Framework\n===================\n\nMulti-jurisdiction regulatory framework for financial compliance.\nDefines compliance rules, requirements, and mappings for different jurisdictions.\n"


class Jurisdiction(Enum):
    """Supported regulatory jurisdictions."""

    EU = "eu"
    US = "us"
    UK = "uk"
    SINGAPORE = "singapore"
    HONG_KONG = "hong_kong"
    AUSTRALIA = "australia"
    CANADA = "canada"
    JAPAN = "japan"
    SWITZERLAND = "switzerland"
    GLOBAL = "global"


class RuleCategory(Enum):
    """Categories of compliance rules."""

    AML = "aml"
    KYC = "kyc"
    DATA_PROTECTION = "data_protection"
    TRANSACTION_MONITORING = "transaction_monitoring"
    REPORTING = "reporting"
    SANCTIONS = "sanctions"
    CONSUMER_PROTECTION = "consumer_protection"
    OPERATIONAL = "operational"


class RuleSeverity(Enum):
    """Severity levels for compliance rules."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceRule:
    """Individual compliance rule definition."""

    rule_id: str
    name: str
    description: str
    jurisdiction: Jurisdiction
    category: RuleCategory
    severity: RuleSeverity
    applicable_entities: List[str]
    requirements: Dict[str, Any]
    penalties: Dict[str, Any]
    effective_date: datetime
    expiry_date: Optional[datetime] = None

    def is_applicable(self, entity_type: str, current_date: datetime = None) -> bool:
        """Check if rule is applicable to entity type and current date."""
        if current_date is None:
            current_date = datetime.now(timezone.utc)
        if entity_type not in self.applicable_entities:
            return False
        if current_date < self.effective_date:
            return False
        if self.expiry_date and current_date > self.expiry_date:
            return False
        return True


@dataclass
class JurisdictionProfile:
    """Profile of regulatory requirements for a jurisdiction."""

    jurisdiction: Jurisdiction
    name: str
    regulatory_bodies: List[str]
    key_regulations: List[str]
    aml_requirements: Dict[str, Any]
    kyc_requirements: Dict[str, Any]
    data_protection_requirements: Dict[str, Any]
    reporting_requirements: Dict[str, Any]
    transaction_limits: Dict[str, Any]
    penalties: Dict[str, Any]


class RegulatoryFramework:
    """
    Multi-jurisdiction regulatory framework for financial compliance.

    Features:
    - Jurisdiction-specific rule management
    - Rule applicability assessment
    - Regulatory requirement mapping
    - Compliance threshold management
    - Cross-jurisdiction harmonization
    """

    def __init__(self) -> None:
        self._rules = {}
        self._jurisdiction_profiles = {}
        self._initialize_framework()

    def _initialize_framework(self) -> object:
        """Initialize the regulatory framework with default rules and profiles."""
        self._initialize_jurisdiction_profiles()
        self._initialize_compliance_rules()

    def _initialize_jurisdiction_profiles(self) -> object:
        """Initialize jurisdiction profiles with regulatory requirements."""
        self._jurisdiction_profiles[Jurisdiction.EU] = JurisdictionProfile(
            jurisdiction=Jurisdiction.EU,
            name="European Union",
            regulatory_bodies=[
                "EBA",
                "ESMA",
                "EIOPA",
                "ECB",
                "National Competent Authorities",
            ],
            key_regulations=["PSD2", "GDPR", "6AMLD", "MiCA", "DORA"],
            aml_requirements={
                "customer_due_diligence": True,
                "enhanced_due_diligence_threshold": 15000,
                "suspicious_transaction_reporting": True,
                "sanctions_screening": True,
                "pep_screening": True,
                "beneficial_ownership": True,
            },
            kyc_requirements={
                "identity_verification": True,
                "address_verification": True,
                "document_verification": True,
                "biometric_verification": False,
                "ongoing_monitoring": True,
            },
            data_protection_requirements={
                "gdpr_compliance": True,
                "consent_management": True,
                "data_minimization": True,
                "right_to_be_forgotten": True,
                "data_portability": True,
                "privacy_by_design": True,
            },
            reporting_requirements={
                "transaction_reporting": True,
                "suspicious_activity_reporting": True,
                "large_transaction_reporting": 10000,
                "cross_border_reporting": 10000,
                "regulatory_reporting_frequency": "monthly",
            },
            transaction_limits={
                "daily_limit": 15000,
                "monthly_limit": 50000,
                "annual_limit": 200000,
                "cash_transaction_limit": 10000,
            },
            penalties={
                "gdpr_max_fine": "4% of annual turnover or €20M",
                "aml_max_fine": "€5M or 10% of annual turnover",
                "psd2_max_fine": "€5M or 10% of annual turnover",
            },
        )
        self._jurisdiction_profiles[Jurisdiction.US] = JurisdictionProfile(
            jurisdiction=Jurisdiction.US,
            name="United States",
            regulatory_bodies=[
                "FinCEN",
                "CFPB",
                "OCC",
                "FDIC",
                "Federal Reserve",
                "SEC",
                "CFTC",
            ],
            key_regulations=["BSA", "USA PATRIOT Act", "FCRA", "CCPA", "Dodd-Frank"],
            aml_requirements={
                "customer_due_diligence": True,
                "enhanced_due_diligence_threshold": 10000,
                "suspicious_transaction_reporting": True,
                "sanctions_screening": True,
                "pep_screening": True,
                "beneficial_ownership": True,
            },
            kyc_requirements={
                "identity_verification": True,
                "address_verification": True,
                "document_verification": True,
                "biometric_verification": False,
                "ongoing_monitoring": True,
            },
            data_protection_requirements={
                "ccpa_compliance": True,
                "consent_management": True,
                "data_minimization": False,
                "right_to_be_forgotten": True,
                "data_portability": True,
                "privacy_by_design": False,
            },
            reporting_requirements={
                "ctr_reporting": True,
                "sar_reporting": True,
                "large_transaction_reporting": 10000,
                "cross_border_reporting": 10000,
                "regulatory_reporting_frequency": "monthly",
            },
            transaction_limits={
                "daily_limit": 10000,
                "monthly_limit": 50000,
                "annual_limit": 200000,
                "cash_transaction_limit": 10000,
            },
            penalties={
                "bsa_civil_penalty": "$25,000 per violation",
                "bsa_criminal_penalty": "$500,000 and/or 5 years imprisonment",
                "ccpa_max_fine": "$7,500 per violation",
            },
        )
        self._jurisdiction_profiles[Jurisdiction.SINGAPORE] = JurisdictionProfile(
            jurisdiction=Jurisdiction.SINGAPORE,
            name="Singapore",
            regulatory_bodies=["MAS", "ACRA", "PDPC"],
            key_regulations=["PSA", "PDPA", "CDSA", "SFA"],
            aml_requirements={
                "customer_due_diligence": True,
                "enhanced_due_diligence_threshold": 20000,
                "suspicious_transaction_reporting": True,
                "sanctions_screening": True,
                "pep_screening": True,
                "beneficial_ownership": True,
            },
            kyc_requirements={
                "identity_verification": True,
                "address_verification": True,
                "document_verification": True,
                "biometric_verification": True,
                "ongoing_monitoring": True,
            },
            data_protection_requirements={
                "pdpa_compliance": True,
                "consent_management": True,
                "data_minimization": True,
                "right_to_be_forgotten": False,
                "data_portability": False,
                "privacy_by_design": True,
            },
            reporting_requirements={
                "transaction_reporting": True,
                "suspicious_activity_reporting": True,
                "large_transaction_reporting": 20000,
                "cross_border_reporting": 20000,
                "regulatory_reporting_frequency": "monthly",
            },
            transaction_limits={
                "daily_limit": 20000,
                "monthly_limit": 100000,
                "annual_limit": 500000,
                "cash_transaction_limit": 20000,
            },
            penalties={
                "pdpa_max_fine": "S$1M",
                "aml_max_fine": "S$1M or 3x benefit derived",
                "psa_max_fine": "S$125,000",
            },
        )
        self._jurisdiction_profiles[Jurisdiction.HONG_KONG] = JurisdictionProfile(
            jurisdiction=Jurisdiction.HONG_KONG,
            name="Hong Kong",
            regulatory_bodies=["HKMA", "SFC", "IA", "PCPD"],
            key_regulations=["AMLO", "PDPO", "SFO"],
            aml_requirements={
                "customer_due_diligence": True,
                "enhanced_due_diligence_threshold": 120000,
                "suspicious_transaction_reporting": True,
                "sanctions_screening": True,
                "pep_screening": True,
                "beneficial_ownership": True,
            },
            kyc_requirements={
                "identity_verification": True,
                "address_verification": True,
                "document_verification": True,
                "biometric_verification": False,
                "ongoing_monitoring": True,
            },
            data_protection_requirements={
                "pdpo_compliance": True,
                "consent_management": True,
                "data_minimization": False,
                "right_to_be_forgotten": False,
                "data_portability": False,
                "privacy_by_design": False,
            },
            reporting_requirements={
                "transaction_reporting": True,
                "suspicious_activity_reporting": True,
                "large_transaction_reporting": 120000,
                "cross_border_reporting": 120000,
                "regulatory_reporting_frequency": "monthly",
            },
            transaction_limits={
                "daily_limit": 120000,
                "monthly_limit": 500000,
                "annual_limit": 2000000,
                "cash_transaction_limit": 120000,
            },
            penalties={
                "pdpo_max_fine": "HK$1M",
                "amlo_max_fine": "HK$1M or 3 years imprisonment",
                "sfo_max_fine": "HK$10M",
            },
        )

    def _initialize_compliance_rules(self) -> object:
        """Initialize compliance rules for all jurisdictions."""
        self._add_eu_rules()
        self._add_us_rules()
        self._add_singapore_rules()
        self._add_hong_kong_rules()
        self._add_global_rules()

    def _add_eu_rules(self) -> object:
        """Add EU-specific compliance rules."""
        self._rules["eu_gdpr_consent"] = ComplianceRule(
            rule_id="eu_gdpr_consent",
            name="GDPR Consent Management",
            description="Ensure valid consent for personal data processing under GDPR",
            jurisdiction=Jurisdiction.EU,
            category=RuleCategory.DATA_PROTECTION,
            severity=RuleSeverity.CRITICAL,
            applicable_entities=["user", "transaction"],
            requirements={
                "explicit_consent": True,
                "consent_withdrawal": True,
                "consent_documentation": True,
                "lawful_basis": [
                    "consent",
                    "contract",
                    "legal_obligation",
                    "vital_interests",
                    "public_task",
                    "legitimate_interests",
                ],
            },
            penalties={
                "max_fine": "4% of annual turnover or €20M",
                "administrative_measures": True,
            },
            effective_date=datetime(2018, 5, 25),
        )
        self._rules["eu_psd2_sca"] = ComplianceRule(
            rule_id="eu_psd2_sca",
            name="PSD2 Strong Customer Authentication",
            description="Implement strong customer authentication for payment transactions",
            jurisdiction=Jurisdiction.EU,
            category=RuleCategory.OPERATIONAL,
            severity=RuleSeverity.HIGH,
            applicable_entities=["transaction"],
            requirements={
                "two_factor_authentication": True,
                "dynamic_linking": True,
                "exemption_thresholds": {
                    "low_value": 30,
                    "contactless": 50,
                    "trusted_beneficiary": True,
                },
            },
            penalties={"max_fine": "€5M or 10% of annual turnover"},
            effective_date=datetime(2019, 9, 14),
        )
        self._rules["eu_6amld_aml"] = ComplianceRule(
            rule_id="eu_6amld_aml",
            name="6AMLD Anti-Money Laundering",
            description="Enhanced AML requirements under 6th Anti-Money Laundering Directive",
            jurisdiction=Jurisdiction.EU,
            category=RuleCategory.AML,
            severity=RuleSeverity.CRITICAL,
            applicable_entities=["user", "transaction"],
            requirements={
                "customer_due_diligence": True,
                "enhanced_due_diligence": True,
                "beneficial_ownership": True,
                "sanctions_screening": True,
                "pep_screening": True,
                "transaction_monitoring": True,
                "suspicious_activity_reporting": True,
            },
            penalties={
                "max_fine": "€5M or 10% of annual turnover",
                "criminal_sanctions": True,
            },
            effective_date=datetime(2021, 6, 3),
        )

    def _add_us_rules(self) -> object:
        """Add US-specific compliance rules."""
        self._rules["us_bsa_ctr"] = ComplianceRule(
            rule_id="us_bsa_ctr",
            name="BSA Currency Transaction Reporting",
            description="Report currency transactions over $10,000",
            jurisdiction=Jurisdiction.US,
            category=RuleCategory.REPORTING,
            severity=RuleSeverity.HIGH,
            applicable_entities=["transaction"],
            requirements={
                "reporting_threshold": 10000,
                "filing_deadline": 15,
                "form_required": "FinCEN Form 104",
                "exemptions": ["bank_to_bank", "government_transactions"],
            },
            penalties={
                "civil_penalty": "$25,000 per violation",
                "criminal_penalty": "$500,000 and/or 5 years imprisonment",
            },
            effective_date=datetime(1970, 10, 26),
        )
        self._rules["us_bsa_sar"] = ComplianceRule(
            rule_id="us_bsa_sar",
            name="BSA Suspicious Activity Reporting",
            description="Report suspicious activities that may indicate money laundering",
            jurisdiction=Jurisdiction.US,
            category=RuleCategory.REPORTING,
            severity=RuleSeverity.CRITICAL,
            applicable_entities=["transaction", "user"],
            requirements={
                "reporting_threshold": 5000,
                "filing_deadline": 30,
                "form_required": "FinCEN Form 111",
                "suspicious_indicators": [
                    "structuring",
                    "unusual_patterns",
                    "high_risk_countries",
                ],
            },
            penalties={
                "civil_penalty": "$25,000 per violation",
                "criminal_penalty": "$500,000 and/or 5 years imprisonment",
            },
            effective_date=datetime(1996, 4, 1),
        )
        self._rules["us_ccpa_privacy"] = ComplianceRule(
            rule_id="us_ccpa_privacy",
            name="CCPA Consumer Privacy Rights",
            description="California Consumer Privacy Act compliance requirements",
            jurisdiction=Jurisdiction.US,
            category=RuleCategory.DATA_PROTECTION,
            severity=RuleSeverity.HIGH,
            applicable_entities=["user"],
            requirements={
                "right_to_know": True,
                "right_to_delete": True,
                "right_to_opt_out": True,
                "non_discrimination": True,
                "privacy_notice": True,
            },
            penalties={
                "civil_penalty": "$7,500 per violation",
                "private_right_of_action": True,
            },
            effective_date=datetime(2020, 1, 1),
        )

    def _add_singapore_rules(self) -> object:
        """Add Singapore-specific compliance rules."""
        self._rules["sg_psa_licensing"] = ComplianceRule(
            rule_id="sg_psa_licensing",
            name="PSA Payment Service Licensing",
            description="Payment Services Act licensing requirements",
            jurisdiction=Jurisdiction.SINGAPORE,
            category=RuleCategory.OPERATIONAL,
            severity=RuleSeverity.CRITICAL,
            applicable_entities=["merchant", "user"],
            requirements={
                "license_required": True,
                "capital_requirements": True,
                "fit_and_proper": True,
                "operational_requirements": True,
            },
            penalties={"max_fine": "S$125,000", "imprisonment": "3 years"},
            effective_date=datetime(2020, 1, 28),
        )
        self._rules["sg_pdpa_consent"] = ComplianceRule(
            rule_id="sg_pdpa_consent",
            name="PDPA Personal Data Protection",
            description="Personal Data Protection Act compliance requirements",
            jurisdiction=Jurisdiction.SINGAPORE,
            category=RuleCategory.DATA_PROTECTION,
            severity=RuleSeverity.HIGH,
            applicable_entities=["user"],
            requirements={
                "consent_required": True,
                "purpose_limitation": True,
                "data_protection_measures": True,
                "breach_notification": True,
            },
            penalties={"max_fine": "S$1M"},
            effective_date=datetime(2014, 7, 2),
        )

    def _add_hong_kong_rules(self) -> object:
        """Add Hong Kong-specific compliance rules."""
        self._rules["hk_amlo_cdd"] = ComplianceRule(
            rule_id="hk_amlo_cdd",
            name="AMLO Customer Due Diligence",
            description="Anti-Money Laundering Ordinance CDD requirements",
            jurisdiction=Jurisdiction.HONG_KONG,
            category=RuleCategory.AML,
            severity=RuleSeverity.HIGH,
            applicable_entities=["user"],
            requirements={
                "customer_identification": True,
                "beneficial_ownership": True,
                "ongoing_monitoring": True,
                "record_keeping": True,
            },
            penalties={"max_fine": "HK$1M", "imprisonment": "3 years"},
            effective_date=datetime(2012, 4, 1),
        )

    def _add_global_rules(self) -> object:
        """Add global/international compliance rules."""
        self._rules["global_fatf_40"] = ComplianceRule(
            rule_id="global_fatf_40",
            name="FATF 40 Recommendations",
            description="Financial Action Task Force 40 Recommendations on AML/CFT",
            jurisdiction=Jurisdiction.GLOBAL,
            category=RuleCategory.AML,
            severity=RuleSeverity.HIGH,
            applicable_entities=["user", "transaction"],
            requirements={
                "risk_based_approach": True,
                "customer_due_diligence": True,
                "record_keeping": True,
                "suspicious_transaction_reporting": True,
                "international_cooperation": True,
            },
            penalties={"varies_by_jurisdiction": True},
            effective_date=datetime(2012, 2, 16),
        )

    def get_applicable_rules(
        self,
        jurisdiction: Jurisdiction,
        entity_type: str,
        current_date: datetime = None,
    ) -> List[ComplianceRule]:
        """Get all applicable rules for a jurisdiction and entity type."""
        if current_date is None:
            current_date = datetime.now(timezone.utc)
        applicable_rules = []
        for rule in self._rules.values():
            if (
                rule.jurisdiction == jurisdiction
                or rule.jurisdiction == Jurisdiction.GLOBAL
            ):
                if rule.is_applicable(entity_type, current_date):
                    applicable_rules.append(rule)
        return applicable_rules

    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """Get a specific rule by ID."""
        return self._rules.get(rule_id)

    def get_jurisdiction_profile(
        self, jurisdiction: Jurisdiction
    ) -> Optional[JurisdictionProfile]:
        """Get jurisdiction profile with regulatory requirements."""
        return self._jurisdiction_profiles.get(jurisdiction)

    def get_all_jurisdictions(self) -> List[Jurisdiction]:
        """Get list of all supported jurisdictions."""
        return list(self._jurisdiction_profiles.keys())

    def get_rules_by_category(
        self, category: RuleCategory, jurisdiction: Jurisdiction = None
    ) -> List[ComplianceRule]:
        """Get rules filtered by category and optionally jurisdiction."""
        filtered_rules = []
        for rule in self._rules.values():
            if rule.category == category:
                if (
                    jurisdiction is None
                    or rule.jurisdiction == jurisdiction
                    or rule.jurisdiction == Jurisdiction.GLOBAL
                ):
                    filtered_rules.append(rule)
        return filtered_rules

    def get_rules_by_severity(
        self, severity: RuleSeverity, jurisdiction: Jurisdiction = None
    ) -> List[ComplianceRule]:
        """Get rules filtered by severity and optionally jurisdiction."""
        filtered_rules = []
        for rule in self._rules.values():
            if rule.severity == severity:
                if (
                    jurisdiction is None
                    or rule.jurisdiction == jurisdiction
                    or rule.jurisdiction == Jurisdiction.GLOBAL
                ):
                    filtered_rules.append(rule)
        return filtered_rules

    def add_custom_rule(self, rule: ComplianceRule) -> object:
        """Add a custom compliance rule."""
        self._rules[rule.rule_id] = rule

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing rule."""
        if rule_id not in self._rules:
            return False
        rule = self._rules[rule_id]
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        return True

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_compliance_requirements(
        self, jurisdiction: Jurisdiction, entity_type: str
    ) -> Dict[str, Any]:
        """Get comprehensive compliance requirements for jurisdiction and entity type."""
        profile = self.get_jurisdiction_profile(jurisdiction)
        rules = self.get_applicable_rules(jurisdiction, entity_type)
        if not profile:
            return {}
        requirements = {
            "jurisdiction": jurisdiction.value,
            "jurisdiction_name": profile.name,
            "regulatory_bodies": profile.regulatory_bodies,
            "key_regulations": profile.key_regulations,
            "applicable_rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "category": rule.category.value,
                    "severity": rule.severity.value,
                    "requirements": rule.requirements,
                }
                for rule in rules
            ],
            "aml_requirements": profile.aml_requirements,
            "kyc_requirements": profile.kyc_requirements,
            "data_protection_requirements": profile.data_protection_requirements,
            "reporting_requirements": profile.reporting_requirements,
            "transaction_limits": profile.transaction_limits,
            "penalties": profile.penalties,
        }
        return requirements

    def validate_transaction_limits(
        self,
        jurisdiction: Jurisdiction,
        amount: float,
        currency: str,
        transaction_type: str = "payment",
    ) -> Dict[str, Any]:
        """Validate transaction against jurisdiction limits."""
        profile = self.get_jurisdiction_profile(jurisdiction)
        if not profile:
            return {
                "valid": False,
                "reason": f"Unsupported jurisdiction: {jurisdiction.value}",
            }
        limits = profile.transaction_limits
        violations = []
        if "daily_limit" in limits and amount > limits["daily_limit"]:
            violations.append(f"Exceeds daily limit of {limits['daily_limit']}")
        if (
            "cash_transaction_limit" in limits
            and transaction_type == "cash"
            and (amount > limits["cash_transaction_limit"])
        ):
            violations.append(
                f"Exceeds cash transaction limit of {limits['cash_transaction_limit']}"
            )
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "limits_applied": limits,
        }

    def get_reporting_requirements(
        self, jurisdiction: Jurisdiction, transaction_amount: float = None
    ) -> Dict[str, Any]:
        """Get reporting requirements for a jurisdiction and transaction amount."""
        profile = self.get_jurisdiction_profile(jurisdiction)
        if not profile:
            return {}
        reporting_reqs = profile.reporting_requirements.copy()
        if transaction_amount:
            if "large_transaction_reporting" in reporting_reqs:
                threshold = reporting_reqs["large_transaction_reporting"]
                reporting_reqs["large_transaction_required"] = (
                    transaction_amount >= threshold
                )
        return reporting_reqs
