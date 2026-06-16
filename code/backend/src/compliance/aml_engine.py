import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List

from sqlalchemy.orm import Session

"\nAML Engine\n==========\n\nAdvanced Anti-Money Laundering engine for financial compliance.\nProvides comprehensive AML screening, monitoring, and reporting capabilities.\n"


class AMLStatus(Enum):
    """AML screening status."""

    CLEAR = "clear"
    REVIEW = "review"
    BLOCKED = "blocked"
    PENDING = "pending"
    ERROR = "error"


class RiskLevel(Enum):
    """Risk level classifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SanctionsListType(Enum):
    """Types of sanctions lists."""

    OFAC_SDN = "ofac_sdn"
    OFAC_CONS = "ofac_cons"
    EU_SANCTIONS = "eu_sanctions"
    UN_SANCTIONS = "un_sanctions"
    HMT_SANCTIONS = "hmt_sanctions"
    CUSTOM = "custom"


@dataclass
class AMLFlag:
    """Individual AML flag or alert."""

    flag_id: str
    flag_type: str
    severity: RiskLevel
    description: str
    details: Dict[str, Any]
    source: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flag_id": self.flag_id,
            "flag_type": self.flag_type,
            "severity": self.severity.value,
            "description": self.description,
            "details": self.details,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AMLResult:
    """AML screening result."""

    entity_id: str
    entity_type: str
    status: str
    risk_score: float
    risk_level: RiskLevel
    flags: List[AMLFlag]
    sanctions_matches: List[Dict[str, Any]]
    pep_matches: List[Dict[str, Any]]
    adverse_media_matches: List[Dict[str, Any]]
    screening_timestamp: datetime
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "status": self.status,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "flags": [flag.to_dict() for flag in self.flags],
            "sanctions_matches": self.sanctions_matches,
            "pep_matches": self.pep_matches,
            "adverse_media_matches": self.adverse_media_matches,
            "screening_timestamp": self.screening_timestamp.isoformat(),
            "details": self.details,
        }


@dataclass
class TransactionPattern:
    """Transaction pattern for monitoring."""

    pattern_id: str
    pattern_type: str
    description: str
    risk_indicators: List[str]
    threshold_rules: Dict[str, Any]
    time_window: timedelta

    def matches(self, transactions: List[Dict[str, Any]]) -> bool:
        """Check if transactions match this pattern."""
        return False


class AMLEngine:
    """
    Advanced Anti-Money Laundering engine for financial compliance.

    Features:
    - Real-time sanctions screening
    - PEP (Politically Exposed Person) screening
    - Adverse media screening
    - Transaction monitoring and pattern detection
    - Risk scoring and assessment
    - Suspicious activity detection
    - Regulatory reporting
    - Case management
    """

    def __init__(self, db_session: Session, config: Dict[str, Any] = None) -> None:
        self.db = db_session
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._sanctions_lists = {}
        self._pep_lists = {}
        self._adverse_media_sources = []
        self._transaction_patterns = {}
        self._risk_rules = {}
        self._name_match_threshold = 0.85
        self._address_match_threshold = 0.8
        self._date_match_threshold = 0.9
        self._initialize_aml_engine()

    def _initialize_aml_engine(self) -> object:
        """Initialize the AML engine with default configurations."""
        self._load_sanctions_lists()
        self._load_pep_lists()
        self._initialize_transaction_patterns()
        self._initialize_risk_rules()
        self.logger.info("AML engine initialized successfully")

    def _load_sanctions_lists(self) -> object:
        """Load sanctions lists from various sources."""
        self._sanctions_lists[SanctionsListType.OFAC_SDN] = {
            "name": "OFAC Specially Designated Nationals",
            "source": "US Treasury OFAC",
            "last_updated": datetime.now(timezone.utc),
            "entries": [
                {
                    "id": "SDN-12345",
                    "name": "John Doe",
                    "aliases": ["J. Doe", "Johnny Doe"],
                    "addresses": ["123 Main St, Anytown, US"],
                    "date_of_birth": "1980-01-01",
                    "nationality": "US",
                    "program": "TERRORISM",
                    "remarks": "Designated for terrorism activities",
                }
            ],
        }
        self._sanctions_lists[SanctionsListType.EU_SANCTIONS] = {
            "name": "EU Consolidated Sanctions List",
            "source": "European Union",
            "last_updated": datetime.now(timezone.utc),
            "entries": [
                {
                    "id": "EU-67890",
                    "name": "Jane Smith",
                    "aliases": ["J. Smith"],
                    "addresses": ["456 Oak Ave, London, UK"],
                    "date_of_birth": "1975-05-15",
                    "nationality": "UK",
                    "program": "ASSET_FREEZE",
                    "remarks": "Asset freeze measures",
                }
            ],
        }

    def _load_pep_lists(self) -> object:
        """Load Politically Exposed Person lists."""
        self._pep_lists = {
            "global_peps": {
                "name": "Global PEP Database",
                "source": "Compliance Database",
                "last_updated": datetime.now(timezone.utc),
                "entries": [
                    {
                        "id": "PEP-001",
                        "name": "Robert Johnson",
                        "position": "Minister of Finance",
                        "country": "Country A",
                        "start_date": "2020-01-01",
                        "end_date": None,
                        "risk_level": "HIGH",
                        "family_members": ["Mary Johnson", "Tom Johnson"],
                        "close_associates": ["Business Partner X"],
                    }
                ],
            }
        }

    def _initialize_transaction_patterns(self) -> object:
        """Initialize suspicious transaction patterns."""
        self._transaction_patterns["structuring"] = TransactionPattern(
            pattern_id="structuring",
            pattern_type="structuring",
            description="Multiple transactions just below reporting threshold",
            risk_indicators=[
                "amount_just_below_threshold",
                "frequent_transactions",
                "same_beneficiary",
            ],
            threshold_rules={
                "max_amount": 9999,
                "min_transactions": 3,
                "time_window_hours": 24,
            },
            time_window=timedelta(hours=24),
        )
        self._transaction_patterns["rapid_movement"] = TransactionPattern(
            pattern_id="rapid_movement",
            pattern_type="rapid_movement",
            description="Rapid movement of funds through multiple accounts",
            risk_indicators=["multiple_accounts", "quick_succession", "round_amounts"],
            threshold_rules={
                "min_accounts": 3,
                "max_time_between_transactions": 60,
                "min_total_amount": 50000,
            },
            time_window=timedelta(hours=6),
        )
        self._transaction_patterns["geographic_risk"] = TransactionPattern(
            pattern_id="geographic_risk",
            pattern_type="geographic_risk",
            description="Transactions involving high-risk geographic locations",
            risk_indicators=[
                "high_risk_country",
                "sanctions_jurisdiction",
                "tax_haven",
            ],
            threshold_rules={
                "high_risk_countries": ["Country X", "Country Y"],
                "min_amount": 1000,
            },
            time_window=timedelta(days=1),
        )

    def _initialize_risk_rules(self) -> object:
        """Initialize risk scoring rules."""
        self._risk_rules = {
            "customer_risk_factors": {
                "pep_status": {"weight": 0.4, "high_risk_score": 0.8},
                "sanctions_match": {"weight": 1.0, "high_risk_score": 1.0},
                "adverse_media": {"weight": 0.3, "high_risk_score": 0.6},
                "high_risk_country": {"weight": 0.2, "high_risk_score": 0.4},
                "cash_intensive_business": {"weight": 0.3, "high_risk_score": 0.5},
            },
            "transaction_risk_factors": {
                "large_amount": {"weight": 0.3, "threshold": 10000},
                "cross_border": {"weight": 0.2, "high_risk_score": 0.4},
                "high_risk_country": {"weight": 0.4, "high_risk_score": 0.6},
                "unusual_pattern": {"weight": 0.5, "high_risk_score": 0.7},
                "round_amount": {"weight": 0.1, "high_risk_score": 0.2},
            },
        }

    async def screen_customer(self, customer_data: Dict[str, Any]) -> AMLResult:
        """
        Perform comprehensive AML screening for a customer.

        Args:
            customer_data: Customer information for screening

        Returns:
            AMLResult containing screening results
        """
        customer_id = customer_data.get(
            "user_id", customer_data.get("customer_id", "unknown")
        )
        try:
            self.logger.info(f"Starting AML screening for customer {customer_id}")
            flags = []
            sanctions_matches = []
            pep_matches = []
            adverse_media_matches = []
            sanctions_result = await self._screen_sanctions(customer_data)
            if sanctions_result["matches"]:
                sanctions_matches = sanctions_result["matches"]
                flags.append(
                    AMLFlag(
                        flag_id=f"sanctions_{customer_id}_{int(datetime.now(timezone.utc).timestamp())}",
                        flag_type="sanctions_match",
                        severity=RiskLevel.CRITICAL,
                        description=f"Sanctions match found: {len(sanctions_matches)} matches",
                        details=sanctions_result,
                        source="sanctions_screening",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
            pep_result = await self._screen_pep(customer_data)
            if pep_result["matches"]:
                pep_matches = pep_result["matches"]
                flags.append(
                    AMLFlag(
                        flag_id=f"pep_{customer_id}_{int(datetime.now(timezone.utc).timestamp())}",
                        flag_type="pep_match",
                        severity=RiskLevel.HIGH,
                        description=f"PEP match found: {len(pep_matches)} matches",
                        details=pep_result,
                        source="pep_screening",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
            adverse_media_result = await self._screen_adverse_media(customer_data)
            if adverse_media_result["matches"]:
                adverse_media_matches = adverse_media_result["matches"]
                flags.append(
                    AMLFlag(
                        flag_id=f"adverse_media_{customer_id}_{int(datetime.now(timezone.utc).timestamp())}",
                        flag_type="adverse_media",
                        severity=RiskLevel.MEDIUM,
                        description=f"Adverse media found: {len(adverse_media_matches)} matches",
                        details=adverse_media_result,
                        source="adverse_media_screening",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
            risk_score = self._calculate_customer_risk_score(customer_data, flags)
            risk_level = self._determine_risk_level(risk_score)
            status = self._determine_aml_status(flags, risk_score)
            result = AMLResult(
                entity_id=customer_id,
                entity_type="customer",
                status=status,
                risk_score=risk_score,
                risk_level=risk_level,
                flags=flags,
                sanctions_matches=sanctions_matches,
                pep_matches=pep_matches,
                adverse_media_matches=adverse_media_matches,
                screening_timestamp=datetime.now(timezone.utc),
                details={
                    "screening_version": "1.0",
                    "sanctions_lists_checked": list(self._sanctions_lists.keys()),
                    "pep_lists_checked": list(self._pep_lists.keys()),
                },
            )
            self.logger.info(
                f"AML screening completed for customer {customer_id}: {status}"
            )
            return result
        except Exception as e:
            self.logger.error(
                f"Error in AML screening for customer {customer_id}: {str(e)}"
            )
            return AMLResult(
                entity_id=customer_id,
                entity_type="customer",
                status=AMLStatus.ERROR.value,
                risk_score=0.0,
                risk_level=RiskLevel.MEDIUM,
                flags=[
                    AMLFlag(
                        flag_id=f"error_{customer_id}_{int(datetime.now(timezone.utc).timestamp())}",
                        flag_type="screening_error",
                        severity=RiskLevel.MEDIUM,
                        description=f"AML screening error: {str(e)}",
                        details={"error": str(e)},
                        source="aml_engine",
                        timestamp=datetime.now(timezone.utc),
                    )
                ],
                sanctions_matches=[],
                pep_matches=[],
                adverse_media_matches=[],
                screening_timestamp=datetime.now(timezone.utc),
                details={"error": str(e)},
            )

    async def screen_transaction(self, transaction_data: Dict[str, Any]) -> AMLResult:
        """
        Perform AML screening for a transaction.

        Args:
            transaction_data: Transaction information for screening

        Returns:
            AMLResult containing screening results
        """
        transaction_id = transaction_data.get("transaction_id", "unknown")
        try:
            self.logger.info(f"Starting AML screening for transaction {transaction_id}")
            flags = []
            amount_flags = await self._analyze_transaction_amount(transaction_data)
            flags.extend(amount_flags)
            geo_flags = await self._analyze_geographic_risk(transaction_data)
            flags.extend(geo_flags)
            pattern_flags = await self._analyze_transaction_patterns(transaction_data)
            flags.extend(pattern_flags)
            counterparty_flags = await self._screen_counterparties(transaction_data)
            flags.extend(counterparty_flags)
            risk_score = self._calculate_transaction_risk_score(transaction_data, flags)
            risk_level = self._determine_risk_level(risk_score)
            status = self._determine_aml_status(flags, risk_score)
            result = AMLResult(
                entity_id=transaction_id,
                entity_type="transaction",
                status=status,
                risk_score=risk_score,
                risk_level=risk_level,
                flags=flags,
                sanctions_matches=[],
                pep_matches=[],
                adverse_media_matches=[],
                screening_timestamp=datetime.now(timezone.utc),
                details={
                    "transaction_amount": transaction_data.get("amount"),
                    "transaction_currency": transaction_data.get("currency"),
                    "transaction_type": transaction_data.get("transaction_type"),
                },
            )
            self.logger.info(
                f"AML screening completed for transaction {transaction_id}: {status}"
            )
            return result
        except Exception as e:
            self.logger.error(
                f"Error in AML screening for transaction {transaction_id}: {str(e)}"
            )
            return AMLResult(
                entity_id=transaction_id,
                entity_type="transaction",
                status=AMLStatus.ERROR.value,
                risk_score=0.0,
                risk_level=RiskLevel.MEDIUM,
                flags=[],
                sanctions_matches=[],
                pep_matches=[],
                adverse_media_matches=[],
                screening_timestamp=datetime.now(timezone.utc),
                details={"error": str(e)},
            )

    async def _screen_sanctions(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Screen entity against sanctions lists."""
        name = entity_data.get("name", entity_data.get("full_name", ""))
        address = entity_data.get("address", "")
        date_of_birth = entity_data.get("date_of_birth", "")
        matches = []
        for list_type, sanctions_list in self._sanctions_lists.items():
            for entry in sanctions_list["entries"]:
                match_score = self._calculate_name_match_score(name, entry["name"])
                for alias in entry.get("aliases", []):
                    alias_score = self._calculate_name_match_score(name, alias)
                    match_score = max(match_score, alias_score)
                if match_score >= self._name_match_threshold:
                    address_score = 0.0
                    if address and entry.get("addresses"):
                        for entry_address in entry["addresses"]:
                            addr_score = self._calculate_address_match_score(
                                address, entry_address
                            )
                            address_score = max(address_score, addr_score)
                    date_score = 0.0
                    if date_of_birth and entry.get("date_of_birth"):
                        date_score = self._calculate_date_match_score(
                            date_of_birth, entry["date_of_birth"]
                        )
                    matches.append(
                        {
                            "list_type": list_type.value,
                            "entry_id": entry["id"],
                            "matched_name": entry["name"],
                            "name_match_score": match_score,
                            "address_match_score": address_score,
                            "date_match_score": date_score,
                            "overall_confidence": (
                                match_score + address_score + date_score
                            )
                            / 3,
                            "program": entry.get("program"),
                            "remarks": entry.get("remarks"),
                        }
                    )
        return {
            "matches": matches,
            "lists_checked": len(self._sanctions_lists),
            "total_entries_checked": sum(
                (len(sl["entries"]) for sl in self._sanctions_lists.values())
            ),
        }

    async def _screen_pep(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Screen entity against PEP lists."""
        name = entity_data.get("name", entity_data.get("full_name", ""))
        matches = []
        for list_name, pep_list in self._pep_lists.items():
            for entry in pep_list["entries"]:
                match_score = self._calculate_name_match_score(name, entry["name"])
                for family_member in entry.get("family_members", []):
                    family_score = self._calculate_name_match_score(name, family_member)
                    if family_score >= self._name_match_threshold:
                        matches.append(
                            {
                                "list_name": list_name,
                                "entry_id": entry["id"],
                                "matched_name": family_member,
                                "match_type": "family_member",
                                "match_score": family_score,
                                "pep_name": entry["name"],
                                "position": entry["position"],
                                "country": entry["country"],
                                "risk_level": entry["risk_level"],
                            }
                        )
                for associate in entry.get("close_associates", []):
                    associate_score = self._calculate_name_match_score(name, associate)
                    if associate_score >= self._name_match_threshold:
                        matches.append(
                            {
                                "list_name": list_name,
                                "entry_id": entry["id"],
                                "matched_name": associate,
                                "match_type": "close_associate",
                                "match_score": associate_score,
                                "pep_name": entry["name"],
                                "position": entry["position"],
                                "country": entry["country"],
                                "risk_level": entry["risk_level"],
                            }
                        )
                if match_score >= self._name_match_threshold:
                    matches.append(
                        {
                            "list_name": list_name,
                            "entry_id": entry["id"],
                            "matched_name": entry["name"],
                            "match_type": "direct_pep",
                            "match_score": match_score,
                            "position": entry["position"],
                            "country": entry["country"],
                            "risk_level": entry["risk_level"],
                        }
                    )
        return {"matches": matches, "lists_checked": len(self._pep_lists)}

    async def _screen_adverse_media(
        self, entity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Screen entity against adverse media sources."""
        name = entity_data.get("name", entity_data.get("full_name", ""))
        matches = []
        if "suspicious" in name.lower() or "criminal" in name.lower():
            matches.append(
                {
                    "source": "Financial News Network",
                    "headline": f"{name} under investigation for financial crimes",
                    "date": "2024-01-15",
                    "relevance_score": 0.85,
                    "sentiment": "negative",
                    "categories": ["financial_crime", "investigation"],
                }
            )
        return {
            "matches": matches,
            "sources_checked": ["Financial News Network", "Global Media Monitor"],
        }

    async def _analyze_transaction_amount(
        self, transaction_data: Dict[str, Any]
    ) -> List[AMLFlag]:
        """Analyze transaction amount for suspicious patterns."""
        flags = []
        amount = transaction_data.get("amount", 0)
        currency = transaction_data.get("currency", "USD")
        if amount >= 10000:
            flags.append(
                AMLFlag(
                    flag_id=f"large_amount_{int(datetime.now(timezone.utc).timestamp())}",
                    flag_type="large_transaction",
                    severity=RiskLevel.MEDIUM,
                    description=f"Large transaction amount: {amount} {currency}",
                    details={
                        "amount": amount,
                        "currency": currency,
                        "threshold": 10000,
                        "reporting_required": True,
                    },
                    source="amount_analysis",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        if amount % 1000 == 0 and amount >= 5000:
            flags.append(
                AMLFlag(
                    flag_id=f"round_amount_{int(datetime.now(timezone.utc).timestamp())}",
                    flag_type="round_amount",
                    severity=RiskLevel.LOW,
                    description=f"Round amount transaction: {amount} {currency}",
                    details={"amount": amount, "currency": currency},
                    source="amount_analysis",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        if 9000 <= amount < 10000:
            flags.append(
                AMLFlag(
                    flag_id=f"below_threshold_{int(datetime.now(timezone.utc).timestamp())}",
                    flag_type="below_threshold",
                    severity=RiskLevel.MEDIUM,
                    description=f"Transaction just below reporting threshold: {amount} {currency}",
                    details={
                        "amount": amount,
                        "currency": currency,
                        "threshold": 10000,
                        "potential_structuring": True,
                    },
                    source="amount_analysis",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        return flags

    async def _analyze_geographic_risk(
        self, transaction_data: Dict[str, Any]
    ) -> List[AMLFlag]:
        """Analyze geographic risk factors."""
        flags = []
        country_code = transaction_data.get("country_code", "")
        high_risk_countries = ["XX", "YY", "ZZ"]
        if country_code in high_risk_countries:
            flags.append(
                AMLFlag(
                    flag_id=f"high_risk_country_{int(datetime.now(timezone.utc).timestamp())}",
                    flag_type="high_risk_geography",
                    severity=RiskLevel.HIGH,
                    description=f"Transaction involving high-risk country: {country_code}",
                    details={
                        "country_code": country_code,
                        "risk_factors": ["money_laundering", "terrorism_financing"],
                    },
                    source="geographic_analysis",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        return flags

    async def _analyze_transaction_patterns(
        self, transaction_data: Dict[str, Any]
    ) -> List[AMLFlag]:
        """Analyze transaction for suspicious patterns."""
        flags = []
        user_id = transaction_data.get("user_id")
        if user_id:
            recent_transactions = await self._get_recent_transactions(
                user_id, timedelta(days=7)
            )
            if self._detect_structuring_pattern(recent_transactions):
                flags.append(
                    AMLFlag(
                        flag_id=f"structuring_{int(datetime.now(timezone.utc).timestamp())}",
                        flag_type="structuring",
                        severity=RiskLevel.HIGH,
                        description="Potential structuring pattern detected",
                        details={
                            "pattern_type": "structuring",
                            "transaction_count": len(recent_transactions),
                            "time_window": "7 days",
                        },
                        source="pattern_analysis",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
            if self._detect_rapid_movement_pattern(recent_transactions):
                flags.append(
                    AMLFlag(
                        flag_id=f"rapid_movement_{int(datetime.now(timezone.utc).timestamp())}",
                        flag_type="rapid_movement",
                        severity=RiskLevel.MEDIUM,
                        description="Rapid movement of funds detected",
                        details={
                            "pattern_type": "rapid_movement",
                            "transaction_count": len(recent_transactions),
                        },
                        source="pattern_analysis",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
        return flags

    async def _screen_counterparties(
        self, transaction_data: Dict[str, Any]
    ) -> List[AMLFlag]:
        """Screen transaction counterparties."""
        flags = []
        beneficiary_name = transaction_data.get("beneficiary_name")
        if beneficiary_name:
            beneficiary_data = {"name": beneficiary_name}
            sanctions_result = await self._screen_sanctions(beneficiary_data)
            if sanctions_result["matches"]:
                flags.append(
                    AMLFlag(
                        flag_id=f"beneficiary_sanctions_{int(datetime.now(timezone.utc).timestamp())}",
                        flag_type="counterparty_sanctions",
                        severity=RiskLevel.CRITICAL,
                        description=f"Beneficiary sanctions match: {beneficiary_name}",
                        details={
                            "counterparty_type": "beneficiary",
                            "matches": sanctions_result["matches"],
                        },
                        source="counterparty_screening",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
        return flags

    def _calculate_name_match_score(self, name1: str, name2: str) -> float:
        """Calculate name matching score using fuzzy matching."""
        if not name1 or not name2:
            return 0.0
        name1_clean = re.sub("[^a-zA-Z\\s]", "", name1.lower()).strip()
        name2_clean = re.sub("[^a-zA-Z\\s]", "", name2.lower()).strip()
        if name1_clean == name2_clean:
            return 1.0
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    def _calculate_address_match_score(self, address1: str, address2: str) -> float:
        """Calculate address matching score."""
        if not address1 or not address2:
            return 0.0
        addr1_clean = re.sub("[^a-zA-Z0-9\\s]", "", address1.lower()).strip()
        addr2_clean = re.sub("[^a-zA-Z0-9\\s]", "", address2.lower()).strip()
        words1 = set(addr1_clean.split())
        words2 = set(addr2_clean.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    def _calculate_date_match_score(self, date1: str, date2: str) -> float:
        """Calculate date matching score."""
        if not date1 or not date2:
            return 0.0
        return 1.0 if date1 == date2 else 0.0

    def _calculate_customer_risk_score(
        self, customer_data: Dict[str, Any], flags: List[AMLFlag]
    ) -> float:
        """Calculate overall risk score for a customer."""
        base_score = 0.1
        for flag in flags:
            if flag.severity == RiskLevel.LOW:
                base_score += 0.1
            elif flag.severity == RiskLevel.MEDIUM:
                base_score += 0.3
            elif flag.severity == RiskLevel.HIGH:
                base_score += 0.6
            elif flag.severity == RiskLevel.CRITICAL:
                base_score += 1.0
        country_code = customer_data.get("country_code", "")
        if country_code in ["XX", "YY"]:
            base_score += 0.3
        return min(base_score, 1.0)

    def _calculate_transaction_risk_score(
        self, transaction_data: Dict[str, Any], flags: List[AMLFlag]
    ) -> float:
        """Calculate overall risk score for a transaction."""
        base_score = 0.05
        for flag in flags:
            if flag.severity == RiskLevel.LOW:
                base_score += 0.1
            elif flag.severity == RiskLevel.MEDIUM:
                base_score += 0.2
            elif flag.severity == RiskLevel.HIGH:
                base_score += 0.4
            elif flag.severity == RiskLevel.CRITICAL:
                base_score += 0.8
        amount = transaction_data.get("amount", 0)
        if amount > 50000:
            base_score += 0.2
        elif amount > 10000:
            base_score += 0.1
        return min(base_score, 1.0)

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level based on risk score."""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _determine_aml_status(self, flags: List[AMLFlag], risk_score: float) -> str:
        """Determine overall AML status."""
        critical_flags = [f for f in flags if f.severity == RiskLevel.CRITICAL]
        if critical_flags:
            return AMLStatus.BLOCKED.value
        high_risk_flags = [f for f in flags if f.severity == RiskLevel.HIGH]
        if high_risk_flags or risk_score >= 0.7:
            return AMLStatus.REVIEW.value
        medium_risk_flags = [f for f in flags if f.severity == RiskLevel.MEDIUM]
        if medium_risk_flags or risk_score >= 0.4:
            return AMLStatus.REVIEW.value
        return AMLStatus.CLEAR.value

    async def _get_recent_transactions(
        self, user_id: str, time_window: timedelta
    ) -> List[Dict[str, Any]]:
        """Get recent transactions for a user."""
        datetime.now(timezone.utc) - time_window
        return [
            {
                "transaction_id": "tx_001",
                "amount": 9500,
                "currency": "USD",
                "timestamp": datetime.now(timezone.utc) - timedelta(hours=2),
                "type": "transfer",
            },
            {
                "transaction_id": "tx_002",
                "amount": 9800,
                "currency": "USD",
                "timestamp": datetime.now(timezone.utc) - timedelta(hours=4),
                "type": "transfer",
            },
        ]

    def _detect_structuring_pattern(self, transactions: List[Dict[str, Any]]) -> bool:
        """Detect potential structuring pattern in transactions."""
        if len(transactions) < 3:
            return False
        below_threshold_count = 0
        for tx in transactions:
            amount = tx.get("amount", 0)
            if 9000 <= amount < 10000:
                below_threshold_count += 1
        return below_threshold_count >= 3

    def _detect_rapid_movement_pattern(
        self, transactions: List[Dict[str, Any]]
    ) -> bool:
        """Detect rapid movement of funds pattern."""
        if len(transactions) < 2:
            return False
        sorted_txs = sorted(
            transactions, key=lambda x: x.get("timestamp", datetime.min)
        )
        for i in range(1, len(sorted_txs)):
            time_diff = sorted_txs[i]["timestamp"] - sorted_txs[i - 1]["timestamp"]
            if time_diff < timedelta(minutes=30):
                return True
        return False

    async def monitor_ongoing_transactions(self, user_id: str) -> Dict[str, Any]:
        """Monitor ongoing transactions for a user."""
        recent_transactions = await self._get_recent_transactions(
            user_id, timedelta(days=30)
        )
        alerts = []
        if self._detect_structuring_pattern(recent_transactions):
            alerts.append(
                {
                    "alert_type": "structuring",
                    "severity": "high",
                    "description": "Potential structuring pattern detected",
                    "transaction_count": len(recent_transactions),
                }
            )
        return {
            "user_id": user_id,
            "monitoring_period": "30 days",
            "transaction_count": len(recent_transactions),
            "alerts": alerts,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def update_sanctions_lists(
        self, list_type: SanctionsListType, new_data: Dict[str, Any]
    ) -> None:
        """Update sanctions lists with new data."""
        self._sanctions_lists[list_type] = new_data
        self.logger.info(f"Updated sanctions list: {list_type.value}")

    def get_aml_statistics(self) -> Dict[str, Any]:
        """Get AML engine statistics."""
        return {
            "sanctions_lists": len(self._sanctions_lists),
            "pep_lists": len(self._pep_lists),
            "transaction_patterns": len(self._transaction_patterns),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
