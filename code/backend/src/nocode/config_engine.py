import copy
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from sqlalchemy.orm import Session

"\nConfiguration Engine\n===================\n\nVisual configuration system for financial applications.\nAllows business users to configure complex settings without coding.\n"


class ConfigType(Enum):
    """Configuration value types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    LIST = "list"
    OBJECT = "object"
    ENUM = "enum"


class ValidationRule(Enum):
    """Configuration validation rules."""

    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    REGEX = "regex"
    CUSTOM = "custom"


@dataclass
class ConfigField:
    """Configuration field definition."""

    field_id: str
    name: str
    description: str
    field_type: ConfigType
    default_value: Any = None
    required: bool = False
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    options: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "name": self.name,
            "description": self.description,
            "field_type": self.field_type.value,
            "default_value": self.default_value,
            "required": self.required,
            "validation_rules": self.validation_rules,
            "options": self.options,
            "metadata": self.metadata,
        }


@dataclass
class ConfigSection:
    """Configuration section containing related fields."""

    section_id: str
    name: str
    description: str
    fields: List[ConfigField] = field(default_factory=list)
    subsections: List["ConfigSection"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "name": self.name,
            "description": self.description,
            "fields": [field.to_dict() for field in self.fields],
            "subsections": [subsection.to_dict() for subsection in self.subsections],
            "metadata": self.metadata,
        }


@dataclass
class ConfigTemplate:
    """Configuration template for specific use cases."""

    template_id: str
    name: str
    description: str
    category: str
    sections: List[ConfigSection] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "sections": [section.to_dict() for section in self.sections],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }


@dataclass
class ConfigInstance:
    """Configuration instance with actual values."""

    instance_id: str
    template_id: str
    name: str
    description: str
    values: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    status: str = "draft"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "values": self.values,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "status": self.status,
            "metadata": self.metadata,
        }


class ConfigurationEngine:
    """
    Visual configuration engine for financial applications.

    Features:
    - Template-based configuration system
    - Visual form builders
    - Field validation and constraints
    - Configuration versioning
    - Import/export capabilities
    - Real-time validation
    - Configuration inheritance
    - Environment-specific configurations
    """

    def __init__(self, db_session: Session, config: Dict[str, Any] = None) -> None:
        self.db = db_session
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._templates = {}
        self._instances = {}
        self._validators = {}
        self._change_listeners = defaultdict(list)
        self._initialize_config_engine()

    def _initialize_config_engine(self) -> object:
        """Initialize the configuration engine."""
        self._create_default_templates()
        self._register_default_validators()
        self.logger.info("Configuration engine initialized successfully")

    def _create_default_templates(self) -> object:
        """Create default configuration templates."""
        payment_template = self._create_payment_processing_template()
        self._templates[payment_template.template_id] = payment_template
        risk_template = self._create_risk_management_template()
        self._templates[risk_template.template_id] = risk_template
        compliance_template = self._create_compliance_template()
        self._templates[compliance_template.template_id] = compliance_template
        analytics_template = self._create_analytics_template()
        self._templates[analytics_template.template_id] = analytics_template

    def _create_payment_processing_template(self) -> ConfigTemplate:
        """Create payment processing configuration template."""
        gateway_section = ConfigSection(
            section_id="payment_gateway",
            name="Payment Gateway",
            description="Configure payment gateway settings",
            fields=[
                ConfigField(
                    field_id="gateway_provider",
                    name="Gateway Provider",
                    description="Select payment gateway provider",
                    field_type=ConfigType.ENUM,
                    required=True,
                    options=["stripe", "paypal", "square", "adyen", "braintree"],
                ),
                ConfigField(
                    field_id="api_key",
                    name="API Key",
                    description="Payment gateway API key",
                    field_type=ConfigType.STRING,
                    required=True,
                    validation_rules={ValidationRule.MIN_LENGTH.value: 10},
                ),
                ConfigField(
                    field_id="webhook_url",
                    name="Webhook URL",
                    description="URL for payment webhooks",
                    field_type=ConfigType.STRING,
                    validation_rules={ValidationRule.REGEX.value: "^https?://.*"},
                ),
                ConfigField(
                    field_id="test_mode",
                    name="Test Mode",
                    description="Enable test mode for development",
                    field_type=ConfigType.BOOLEAN,
                    default_value=True,
                ),
            ],
        )
        limits_section = ConfigSection(
            section_id="transaction_limits",
            name="Transaction Limits",
            description="Configure transaction limits and thresholds",
            fields=[
                ConfigField(
                    field_id="daily_limit",
                    name="Daily Transaction Limit",
                    description="Maximum daily transaction amount",
                    field_type=ConfigType.FLOAT,
                    default_value=10000.0,
                    validation_rules={ValidationRule.MIN_VALUE.value: 0},
                ),
                ConfigField(
                    field_id="single_transaction_limit",
                    name="Single Transaction Limit",
                    description="Maximum single transaction amount",
                    field_type=ConfigType.FLOAT,
                    default_value=5000.0,
                    validation_rules={ValidationRule.MIN_VALUE.value: 0},
                ),
                ConfigField(
                    field_id="monthly_limit",
                    name="Monthly Transaction Limit",
                    description="Maximum monthly transaction amount",
                    field_type=ConfigType.FLOAT,
                    default_value=100000.0,
                    validation_rules={ValidationRule.MIN_VALUE.value: 0},
                ),
            ],
        )
        return ConfigTemplate(
            template_id="payment_processing",
            name="Payment Processing Configuration",
            description="Configure payment processing settings and limits",
            category="payments",
            sections=[gateway_section, limits_section],
        )

    def _create_risk_management_template(self) -> ConfigTemplate:
        """Create risk management configuration template."""
        scoring_section = ConfigSection(
            section_id="risk_scoring",
            name="Risk Scoring",
            description="Configure risk scoring parameters",
            fields=[
                ConfigField(
                    field_id="enable_ml_scoring",
                    name="Enable ML Scoring",
                    description="Use machine learning for risk scoring",
                    field_type=ConfigType.BOOLEAN,
                    default_value=True,
                ),
                ConfigField(
                    field_id="risk_threshold_low",
                    name="Low Risk Threshold",
                    description="Threshold for low risk classification",
                    field_type=ConfigType.FLOAT,
                    default_value=0.3,
                    validation_rules={
                        ValidationRule.MIN_VALUE.value: 0.0,
                        ValidationRule.MAX_VALUE.value: 1.0,
                    },
                ),
                ConfigField(
                    field_id="risk_threshold_medium",
                    name="Medium Risk Threshold",
                    description="Threshold for medium risk classification",
                    field_type=ConfigType.FLOAT,
                    default_value=0.6,
                    validation_rules={
                        ValidationRule.MIN_VALUE.value: 0.0,
                        ValidationRule.MAX_VALUE.value: 1.0,
                    },
                ),
                ConfigField(
                    field_id="risk_threshold_high",
                    name="High Risk Threshold",
                    description="Threshold for high risk classification",
                    field_type=ConfigType.FLOAT,
                    default_value=0.8,
                    validation_rules={
                        ValidationRule.MIN_VALUE.value: 0.0,
                        ValidationRule.MAX_VALUE.value: 1.0,
                    },
                ),
            ],
        )
        fraud_section = ConfigSection(
            section_id="fraud_detection",
            name="Fraud Detection",
            description="Configure fraud detection settings",
            fields=[
                ConfigField(
                    field_id="enable_velocity_checks",
                    name="Enable Velocity Checks",
                    description="Check transaction velocity patterns",
                    field_type=ConfigType.BOOLEAN,
                    default_value=True,
                ),
                ConfigField(
                    field_id="velocity_time_window",
                    name="Velocity Time Window (minutes)",
                    description="Time window for velocity checks",
                    field_type=ConfigType.INTEGER,
                    default_value=60,
                    validation_rules={ValidationRule.MIN_VALUE.value: 1},
                ),
                ConfigField(
                    field_id="max_transactions_per_window",
                    name="Max Transactions per Window",
                    description="Maximum transactions allowed in time window",
                    field_type=ConfigType.INTEGER,
                    default_value=10,
                    validation_rules={ValidationRule.MIN_VALUE.value: 1},
                ),
                ConfigField(
                    field_id="enable_geolocation_checks",
                    name="Enable Geolocation Checks",
                    description="Check for unusual geographic patterns",
                    field_type=ConfigType.BOOLEAN,
                    default_value=True,
                ),
            ],
        )
        return ConfigTemplate(
            template_id="risk_management",
            name="Risk Management Configuration",
            description="Configure risk scoring and fraud detection",
            category="risk",
            sections=[scoring_section, fraud_section],
        )

    def _create_compliance_template(self) -> ConfigTemplate:
        """Create compliance configuration template."""
        regulatory_section = ConfigSection(
            section_id="regulatory_settings",
            name="Regulatory Settings",
            description="Configure regulatory compliance settings",
            fields=[
                ConfigField(
                    field_id="jurisdiction",
                    name="Primary Jurisdiction",
                    description="Primary regulatory jurisdiction",
                    field_type=ConfigType.ENUM,
                    required=True,
                    options=["US", "EU", "UK", "APAC", "GLOBAL"],
                ),
                ConfigField(
                    field_id="enable_gdpr",
                    name="Enable GDPR Compliance",
                    description="Enable GDPR data protection features",
                    field_type=ConfigType.BOOLEAN,
                    default_value=False,
                ),
                ConfigField(
                    field_id="enable_pci_dss",
                    name="Enable PCI DSS Compliance",
                    description="Enable PCI DSS payment card security",
                    field_type=ConfigType.BOOLEAN,
                    default_value=True,
                ),
                ConfigField(
                    field_id="data_retention_days",
                    name="Data Retention Period (days)",
                    description="Number of days to retain customer data",
                    field_type=ConfigType.INTEGER,
                    default_value=2555,
                    validation_rules={ValidationRule.MIN_VALUE.value: 1},
                ),
            ],
        )
        aml_section = ConfigSection(
            section_id="aml_kyc",
            name="AML/KYC Settings",
            description="Configure anti-money laundering and KYC settings",
            fields=[
                ConfigField(
                    field_id="enable_kyc_verification",
                    name="Enable KYC Verification",
                    description="Require KYC verification for new customers",
                    field_type=ConfigType.BOOLEAN,
                    default_value=True,
                ),
                ConfigField(
                    field_id="kyc_verification_level",
                    name="KYC Verification Level",
                    description="Level of KYC verification required",
                    field_type=ConfigType.ENUM,
                    default_value="standard",
                    options=["basic", "standard", "enhanced"],
                ),
                ConfigField(
                    field_id="suspicious_activity_threshold",
                    name="Suspicious Activity Threshold",
                    description="Transaction amount threshold for suspicious activity reporting",
                    field_type=ConfigType.FLOAT,
                    default_value=10000.0,
                    validation_rules={ValidationRule.MIN_VALUE.value: 0},
                ),
                ConfigField(
                    field_id="enable_sanctions_screening",
                    name="Enable Sanctions Screening",
                    description="Screen customers against sanctions lists",
                    field_type=ConfigType.BOOLEAN,
                    default_value=True,
                ),
            ],
        )
        return ConfigTemplate(
            template_id="compliance",
            name="Compliance Configuration",
            description="Configure regulatory compliance and AML/KYC settings",
            category="compliance",
            sections=[regulatory_section, aml_section],
        )

    def _create_analytics_template(self) -> ConfigTemplate:
        """Create analytics configuration template."""
        reporting_section = ConfigSection(
            section_id="reporting",
            name="Reporting Settings",
            description="Configure reporting and analytics settings",
            fields=[
                ConfigField(
                    field_id="enable_real_time_analytics",
                    name="Enable Real-time Analytics",
                    description="Enable real-time data processing and analytics",
                    field_type=ConfigType.BOOLEAN,
                    default_value=True,
                ),
                ConfigField(
                    field_id="data_refresh_interval",
                    name="Data Refresh Interval (minutes)",
                    description="How often to refresh analytics data",
                    field_type=ConfigType.INTEGER,
                    default_value=15,
                    validation_rules={ValidationRule.MIN_VALUE.value: 1},
                ),
                ConfigField(
                    field_id="enable_automated_reports",
                    name="Enable Automated Reports",
                    description="Generate and send reports automatically",
                    field_type=ConfigType.BOOLEAN,
                    default_value=True,
                ),
                ConfigField(
                    field_id="report_recipients",
                    name="Report Recipients",
                    description="Email addresses for automated reports",
                    field_type=ConfigType.LIST,
                    default_value=[],
                ),
            ],
        )
        dashboard_section = ConfigSection(
            section_id="dashboard",
            name="Dashboard Settings",
            description="Configure dashboard and visualization settings",
            fields=[
                ConfigField(
                    field_id="default_dashboard_layout",
                    name="Default Dashboard Layout",
                    description="Default layout for user dashboards",
                    field_type=ConfigType.ENUM,
                    default_value="grid",
                    options=["grid", "list", "cards"],
                ),
                ConfigField(
                    field_id="enable_custom_dashboards",
                    name="Enable Custom Dashboards",
                    description="Allow users to create custom dashboards",
                    field_type=ConfigType.BOOLEAN,
                    default_value=True,
                ),
                ConfigField(
                    field_id="max_dashboard_widgets",
                    name="Max Dashboard Widgets",
                    description="Maximum number of widgets per dashboard",
                    field_type=ConfigType.INTEGER,
                    default_value=20,
                    validation_rules={ValidationRule.MIN_VALUE.value: 1},
                ),
            ],
        )
        return ConfigTemplate(
            template_id="analytics",
            name="Analytics Configuration",
            description="Configure analytics, reporting, and dashboard settings",
            category="analytics",
            sections=[reporting_section, dashboard_section],
        )

    def _register_default_validators(self) -> object:
        """Register default field validators."""

        def validate_required(value: Any, rule_value: bool) -> bool:
            if rule_value and (value is None or value == ""):
                return False
            return True

        def validate_min_length(value: str, rule_value: int) -> bool:
            return len(str(value)) >= rule_value

        def validate_max_length(value: str, rule_value: int) -> bool:
            return len(str(value)) <= rule_value

        def validate_min_value(
            value: Union[int, float], rule_value: Union[int, float]
        ) -> bool:
            return float(value) >= float(rule_value)

        def validate_max_value(
            value: Union[int, float], rule_value: Union[int, float]
        ) -> bool:
            return float(value) <= float(rule_value)

        def validate_regex(value: str, rule_value: str) -> bool:
            import re

            return bool(re.match(rule_value, str(value)))

        self._validators[ValidationRule.REQUIRED.value] = validate_required
        self._validators[ValidationRule.MIN_LENGTH.value] = validate_min_length
        self._validators[ValidationRule.MAX_LENGTH.value] = validate_max_length
        self._validators[ValidationRule.MIN_VALUE.value] = validate_min_value
        self._validators[ValidationRule.MAX_VALUE.value] = validate_max_value
        self._validators[ValidationRule.REGEX.value] = validate_regex

    def create_template(
        self, name: str, description: str, category: str, sections: List[ConfigSection]
    ) -> str:
        """
        Create a new configuration template.

        Args:
            name: Template name
            description: Template description
            category: Template category
            sections: List of configuration sections

        Returns:
            Template ID
        """
        template_id = str(uuid.uuid4())
        template = ConfigTemplate(
            template_id=template_id,
            name=name,
            description=description,
            category=category,
            sections=sections,
        )
        self._templates[template_id] = template
        self.logger.info(f"Created configuration template: {name}")
        return template_id

    def get_template(self, template_id: str) -> Optional[ConfigTemplate]:
        """Get configuration template by ID."""
        return self._templates.get(template_id)

    def list_templates(self, category: str = None) -> List[ConfigTemplate]:
        """
        List configuration templates.

        Args:
            category: Filter by category

        Returns:
            List of templates
        """
        templates = list(self._templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        templates.sort(key=lambda x: x.name)
        return templates

    def create_instance(
        self,
        template_id: str,
        name: str,
        description: str,
        values: Dict[str, Any] = None,
        created_by: str = None,
    ) -> str:
        """
        Create a configuration instance from template.

        Args:
            template_id: Template to use
            name: Instance name
            description: Instance description
            values: Initial configuration values
            created_by: User who created the instance

        Returns:
            Instance ID
        """
        if template_id not in self._templates:
            raise ValueError(f"Template not found: {template_id}")
        instance_id = str(uuid.uuid4())
        if values:
            validation_errors = self.validate_values(template_id, values)
            if validation_errors:
                raise ValueError(f"Validation errors: {validation_errors}")
        instance = ConfigInstance(
            instance_id=instance_id,
            template_id=template_id,
            name=name,
            description=description,
            values=values or {},
            created_by=created_by,
        )
        self._instances[instance_id] = instance
        self._notify_change_listeners(instance_id, "created", instance.values)
        self.logger.info(f"Created configuration instance: {name}")
        return instance_id

    def get_instance(self, instance_id: str) -> Optional[ConfigInstance]:
        """Get configuration instance by ID."""
        return self._instances.get(instance_id)

    def update_instance(
        self, instance_id: str, values: Dict[str, Any], updated_by: str = None
    ) -> bool:
        """
        Update configuration instance values.

        Args:
            instance_id: Instance to update
            values: New configuration values
            updated_by: User who updated the instance

        Returns:
            True if updated successfully
        """
        if instance_id not in self._instances:
            return False
        instance = self._instances[instance_id]
        validation_errors = self.validate_values(instance.template_id, values)
        if validation_errors:
            raise ValueError(f"Validation errors: {validation_errors}")
        old_values = copy.deepcopy(instance.values)
        instance.values.update(values)
        instance.updated_at = datetime.now(timezone.utc)
        self._notify_change_listeners(
            instance_id, "updated", instance.values, old_values
        )
        self.logger.info(f"Updated configuration instance: {instance_id}")
        return True

    def validate_values(self, template_id: str, values: Dict[str, Any]) -> List[str]:
        """
        Validate configuration values against template.

        Args:
            template_id: Template to validate against
            values: Values to validate

        Returns:
            List of validation error messages
        """
        template = self._templates.get(template_id)
        if not template:
            return [f"Template not found: {template_id}"]
        errors = []
        all_fields = {}
        for section in template.sections:
            self._collect_fields(section, all_fields)
        for field_id, field_obj in all_fields.items():
            value = values.get(field_id)
            if field_obj.required and (value is None or value == ""):
                errors.append(f"Field '{field_obj.name}' is required")
                continue
            if value is None or value == "":
                continue
            if not self._validate_type(value, field_obj.field_type):
                errors.append(f"Field '{field_obj.name}' has invalid type")
                continue
            for rule_name, rule_value in field_obj.validation_rules.items():
                validator = self._validators.get(rule_name)
                if validator and (not validator(value, rule_value)):
                    errors.append(
                        f"Field '{field_obj.name}' failed validation rule: {rule_name}"
                    )
        return errors

    def _collect_fields(
        self, section: ConfigSection, fields_dict: Dict[str, ConfigField]
    ) -> object:
        """Recursively collect all fields from section and subsections."""
        for field_obj in section.fields:
            fields_dict[field_obj.field_id] = field_obj
        for subsection in section.subsections:
            self._collect_fields(subsection, fields_dict)

    def _validate_type(self, value: Any, field_type: ConfigType) -> bool:
        """Validate value type."""
        try:
            if field_type == ConfigType.STRING:
                return isinstance(value, str)
            elif field_type == ConfigType.INTEGER:
                return isinstance(value, int) or (
                    isinstance(value, str) and value.isdigit()
                )
            elif field_type == ConfigType.FLOAT:
                return isinstance(value, (int, float)) or (
                    isinstance(value, str) and value.replace(".", "").isdigit()
                )
            elif field_type == ConfigType.BOOLEAN:
                return isinstance(value, bool) or value in [
                    "true",
                    "false",
                    "True",
                    "False",
                ]
            elif field_type == ConfigType.LIST:
                return isinstance(value, list)
            elif field_type == ConfigType.OBJECT:
                return isinstance(value, dict)
            elif field_type == ConfigType.ENUM:
                return True
            else:
                return True
        except Exception:
            return False

    def register_change_listener(self, instance_id: str, callback: Callable) -> object:
        """Register a callback for configuration changes."""
        self._change_listeners[instance_id].append(callback)

    def _notify_change_listeners(
        self,
        instance_id: str,
        action: str,
        new_values: Dict[str, Any],
        old_values: Dict[str, Any] = None,
    ) -> object:
        """Notify registered change listeners."""
        for callback in self._change_listeners[instance_id]:
            try:
                callback(instance_id, action, new_values, old_values)
            except Exception as e:
                self.logger.error(f"Error in change listener: {str(e)}")

    def export_instance(self, instance_id: str) -> Dict[str, Any]:
        """Export configuration instance to dictionary."""
        instance = self._instances.get(instance_id)
        if not instance:
            return {}
        template = self._templates.get(instance.template_id)
        return {
            "instance": instance.to_dict(),
            "template": template.to_dict() if template else None,
        }

    def import_instance(self, data: Dict[str, Any], created_by: str = None) -> str:
        """Import configuration instance from dictionary."""
        instance_data = data.get("instance", {})
        template_data = data.get("template")
        template_id = instance_data.get("template_id")
        if template_data and template_id not in self._templates:
            self._import_template(template_data)
        instance_id = self.create_instance(
            template_id=template_id,
            name=instance_data.get("name", "Imported Configuration"),
            description=instance_data.get("description", ""),
            values=instance_data.get("values", {}),
            created_by=created_by,
        )
        return instance_id

    def _import_template(self, template_data: Dict[str, Any]) -> object:
        """Import template from dictionary."""
        sections = []
        for section_data in template_data.get("sections", []):
            section = self._dict_to_section(section_data)
            sections.append(section)
        template = ConfigTemplate(
            template_id=template_data["template_id"],
            name=template_data["name"],
            description=template_data["description"],
            category=template_data["category"],
            sections=sections,
            version=template_data.get("version", "1.0.0"),
            metadata=template_data.get("metadata", {}),
        )
        self._templates[template.template_id] = template

    def _dict_to_section(self, section_data: Dict[str, Any]) -> ConfigSection:
        """Convert dictionary to ConfigSection."""
        fields = []
        for field_data in section_data.get("fields", []):
            field = ConfigField(
                field_id=field_data["field_id"],
                name=field_data["name"],
                description=field_data["description"],
                field_type=ConfigType(field_data["field_type"]),
                default_value=field_data.get("default_value"),
                required=field_data.get("required", False),
                validation_rules=field_data.get("validation_rules", {}),
                options=field_data.get("options", []),
                metadata=field_data.get("metadata", {}),
            )
            fields.append(field)
        subsections = []
        for subsection_data in section_data.get("subsections", []):
            subsection = self._dict_to_section(subsection_data)
            subsections.append(subsection)
        return ConfigSection(
            section_id=section_data["section_id"],
            name=section_data["name"],
            description=section_data["description"],
            fields=fields,
            subsections=subsections,
            metadata=section_data.get("metadata", {}),
        )

    def list_instances(
        self, template_id: str = None, status: str = None
    ) -> List[ConfigInstance]:
        """
        List configuration instances.

        Args:
            template_id: Filter by template
            status: Filter by status

        Returns:
            List of instances
        """
        instances = list(self._instances.values())
        if template_id:
            instances = [i for i in instances if i.template_id == template_id]
        if status:
            instances = [i for i in instances if i.status == status]
        instances.sort(key=lambda x: x.created_at, reverse=True)
        return instances

    def delete_instance(self, instance_id: str) -> bool:
        """Delete configuration instance."""
        if instance_id not in self._instances:
            return False
        del self._instances[instance_id]
        if instance_id in self._change_listeners:
            del self._change_listeners[instance_id]
        self.logger.info(f"Deleted configuration instance: {instance_id}")
        return True

    def get_configuration_statistics(self) -> Dict[str, Any]:
        """Get configuration engine statistics."""
        template_categories = defaultdict(int)
        instance_statuses = defaultdict(int)
        for template in self._templates.values():
            template_categories[template.category] += 1
        for instance in self._instances.values():
            instance_statuses[instance.status] += 1
        return {
            "total_templates": len(self._templates),
            "total_instances": len(self._instances),
            "template_categories": dict(template_categories),
            "instance_statuses": dict(instance_statuses),
            "registered_validators": len(self._validators),
            "change_listeners": sum(
                (len(listeners) for listeners in self._change_listeners.values())
            ),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
