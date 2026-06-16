import copy
import logging
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

"\nRule Engine\n===========\n\nBusiness rule engine for financial applications.\nAllows business users to define and manage complex business rules without coding.\n"


class RuleType(Enum):
    """Types of business rules."""

    VALIDATION = "validation"
    CALCULATION = "calculation"
    DECISION = "decision"
    TRANSFORMATION = "transformation"
    NOTIFICATION = "notification"
    WORKFLOW = "workflow"


class OperatorType(Enum):
    """Rule condition operators."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX_MATCH = "regex_match"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"


class ActionType(Enum):
    """Rule action types."""

    SET_VALUE = "set_value"
    CALCULATE = "calculate"
    SEND_EMAIL = "send_email"
    CREATE_TASK = "create_task"
    TRIGGER_WORKFLOW = "trigger_workflow"
    LOG_EVENT = "log_event"
    BLOCK_TRANSACTION = "block_transaction"
    REQUIRE_APPROVAL = "require_approval"
    UPDATE_STATUS = "update_status"


@dataclass
class RuleCondition:
    """Individual rule condition."""

    condition_id: str
    field_name: str
    operator: OperatorType
    value: Any
    data_type: str = "string"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "field_name": self.field_name,
            "operator": self.operator.value,
            "value": self.value,
            "data_type": self.data_type,
            "metadata": self.metadata,
        }


@dataclass
class RuleAction:
    """Rule action to execute when conditions are met."""

    action_id: str
    action_type: ActionType
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "parameters": self.parameters,
            "metadata": self.metadata,
        }


@dataclass
class BusinessRule:
    """Complete business rule definition."""

    rule_id: str
    name: str
    description: str
    rule_type: RuleType
    conditions: List[RuleCondition] = field(default_factory=list)
    actions: List[RuleAction] = field(default_factory=list)
    condition_logic: str = "AND"
    priority: int = 100
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type.value,
            "conditions": [condition.to_dict() for condition in self.conditions],
            "actions": [action.to_dict() for action in self.actions],
            "condition_logic": self.condition_logic,
            "priority": self.priority,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class RuleExecution:
    """Rule execution result."""

    execution_id: str
    rule_id: str
    executed_at: datetime
    input_data: Dict[str, Any]
    conditions_met: bool
    executed_actions: List[str]
    execution_time_ms: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "rule_id": self.rule_id,
            "executed_at": self.executed_at.isoformat(),
            "input_data": self.input_data,
            "conditions_met": self.conditions_met,
            "executed_actions": self.executed_actions,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class RuleEngine:
    """
    Business rule engine for financial applications.

    Features:
    - Visual rule builder interface
    - Complex condition logic (AND, OR, custom expressions)
    - Multiple action types
    - Rule prioritization and ordering
    - Real-time rule execution
    - Rule performance monitoring
    - Rule versioning and history
    - Template-based rule creation
    - Bulk rule operations
    - Rule testing and simulation
    """

    def __init__(self, db_session: Session, config: Dict[str, Any] = None) -> None:
        self.db = db_session
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._rules = {}
        self._rule_executions = []
        self._operators = {}
        self._action_handlers = {}
        self._rule_templates = {}
        self._execution_stats = defaultdict(list)
        self._initialize_rule_engine()

    def _initialize_rule_engine(self) -> object:
        """Initialize the rule engine."""
        self._register_operators()
        self._register_action_handlers()
        self._create_default_templates()
        self.logger.info("Rule engine initialized successfully")

    def _register_operators(self) -> object:
        """Register rule condition operators."""
        self._operators[OperatorType.EQUALS] = lambda a, b: a == b
        self._operators[OperatorType.NOT_EQUALS] = lambda a, b: a != b
        self._operators[OperatorType.GREATER_THAN] = lambda a, b: float(a) > float(b)
        self._operators[OperatorType.LESS_THAN] = lambda a, b: float(a) < float(b)
        self._operators[OperatorType.GREATER_EQUAL] = lambda a, b: float(a) >= float(b)
        self._operators[OperatorType.LESS_EQUAL] = lambda a, b: float(a) <= float(b)
        self._operators[OperatorType.CONTAINS] = lambda a, b: str(b) in str(a)
        self._operators[OperatorType.NOT_CONTAINS] = lambda a, b: str(b) not in str(a)
        self._operators[OperatorType.STARTS_WITH] = lambda a, b: str(a).startswith(
            str(b)
        )
        self._operators[OperatorType.ENDS_WITH] = lambda a, b: str(a).endswith(str(b))
        self._operators[OperatorType.REGEX_MATCH] = lambda a, b: bool(
            re.match(str(b), str(a))
        )
        self._operators[OperatorType.IN_LIST] = lambda a, b: a in (
            b if isinstance(b, list) else [b]
        )
        self._operators[OperatorType.NOT_IN_LIST] = lambda a, b: a not in (
            b if isinstance(b, list) else [b]
        )
        self._operators[OperatorType.IS_NULL] = lambda a, b: a is None
        self._operators[OperatorType.IS_NOT_NULL] = lambda a, b: a is not None
        self._operators[OperatorType.BETWEEN] = lambda a, b: (
            b[0] <= float(a) <= b[1] if isinstance(b, list) and len(b) == 2 else False
        )

    def _register_action_handlers(self) -> object:
        """Register rule action handlers."""
        self._action_handlers[ActionType.SET_VALUE] = self._handle_set_value_action
        self._action_handlers[ActionType.CALCULATE] = self._handle_calculate_action
        self._action_handlers[ActionType.SEND_EMAIL] = self._handle_send_email_action
        self._action_handlers[ActionType.CREATE_TASK] = self._handle_create_task_action
        self._action_handlers[ActionType.TRIGGER_WORKFLOW] = (
            self._handle_trigger_workflow_action
        )
        self._action_handlers[ActionType.LOG_EVENT] = self._handle_log_event_action
        self._action_handlers[ActionType.BLOCK_TRANSACTION] = (
            self._handle_block_transaction_action
        )
        self._action_handlers[ActionType.REQUIRE_APPROVAL] = (
            self._handle_require_approval_action
        )
        self._action_handlers[ActionType.UPDATE_STATUS] = (
            self._handle_update_status_action
        )

    def _create_default_templates(self) -> object:
        """Create default rule templates."""
        transaction_limit_rule = self._create_transaction_limit_template()
        self._rule_templates[transaction_limit_rule.rule_id] = transaction_limit_rule
        fraud_detection_rule = self._create_fraud_detection_template()
        self._rule_templates[fraud_detection_rule.rule_id] = fraud_detection_rule
        customer_tier_rule = self._create_customer_tier_template()
        self._rule_templates[customer_tier_rule.rule_id] = customer_tier_rule

    def _create_transaction_limit_template(self) -> BusinessRule:
        """Create transaction limit rule template."""
        conditions = [
            RuleCondition(
                condition_id="amount_check",
                field_name="transaction_amount",
                operator=OperatorType.GREATER_THAN,
                value=10000,
                data_type="number",
            )
        ]
        actions = [
            RuleAction(
                action_id="block_transaction",
                action_type=ActionType.BLOCK_TRANSACTION,
                parameters={
                    "reason": "Transaction amount exceeds limit",
                    "notify_customer": True,
                },
            ),
            RuleAction(
                action_id="require_approval",
                action_type=ActionType.REQUIRE_APPROVAL,
                parameters={"approver_role": "manager", "timeout_hours": 24},
            ),
        ]
        return BusinessRule(
            rule_id="transaction_limit_template",
            name="Transaction Limit Check",
            description="Block transactions exceeding specified limits",
            rule_type=RuleType.VALIDATION,
            conditions=conditions,
            actions=actions,
            category="transaction_limits",
            tags=["transaction", "limit", "validation"],
        )

    def _create_fraud_detection_template(self) -> BusinessRule:
        """Create fraud detection rule template."""
        conditions = [
            RuleCondition(
                condition_id="risk_score_check",
                field_name="fraud_risk_score",
                operator=OperatorType.GREATER_THAN,
                value=0.8,
                data_type="number",
            ),
            RuleCondition(
                condition_id="velocity_check",
                field_name="transaction_count_1h",
                operator=OperatorType.GREATER_THAN,
                value=10,
                data_type="number",
            ),
        ]
        actions = [
            RuleAction(
                action_id="block_transaction",
                action_type=ActionType.BLOCK_TRANSACTION,
                parameters={
                    "reason": "High fraud risk detected",
                    "notify_security": True,
                },
            ),
            RuleAction(
                action_id="log_fraud_event",
                action_type=ActionType.LOG_EVENT,
                parameters={"event_type": "fraud_detection", "severity": "high"},
            ),
        ]
        return BusinessRule(
            rule_id="fraud_detection_template",
            name="Fraud Detection",
            description="Detect and block potentially fraudulent transactions",
            rule_type=RuleType.DECISION,
            conditions=conditions,
            actions=actions,
            condition_logic="OR",
            category="fraud_detection",
            tags=["fraud", "security", "risk"],
        )

    def _create_customer_tier_template(self) -> BusinessRule:
        """Create customer tier rule template."""
        conditions = [
            RuleCondition(
                condition_id="balance_check",
                field_name="account_balance",
                operator=OperatorType.GREATER_EQUAL,
                value=100000,
                data_type="number",
            ),
            RuleCondition(
                condition_id="tenure_check",
                field_name="customer_tenure_months",
                operator=OperatorType.GREATER_EQUAL,
                value=12,
                data_type="number",
            ),
        ]
        actions = [
            RuleAction(
                action_id="upgrade_tier",
                action_type=ActionType.SET_VALUE,
                parameters={"field": "customer_tier", "value": "premium"},
            ),
            RuleAction(
                action_id="send_upgrade_email",
                action_type=ActionType.SEND_EMAIL,
                parameters={
                    "template": "tier_upgrade_notification",
                    "recipient_field": "customer_email",
                },
            ),
        ]
        return BusinessRule(
            rule_id="customer_tier_template",
            name="Customer Tier Upgrade",
            description="Automatically upgrade customer tier based on criteria",
            rule_type=RuleType.CALCULATION,
            conditions=conditions,
            actions=actions,
            condition_logic="AND",
            category="customer_management",
            tags=["customer", "tier", "upgrade"],
        )

    def create_rule(
        self,
        name: str,
        description: str,
        rule_type: RuleType,
        category: str = "general",
        created_by: str = None,
    ) -> str:
        """
        Create a new business rule.

        Args:
            name: Rule name
            description: Rule description
            rule_type: Type of rule
            category: Rule category
            created_by: User who created the rule

        Returns:
            Rule ID
        """
        rule_id = str(uuid.uuid4())
        rule = BusinessRule(
            rule_id=rule_id,
            name=name,
            description=description,
            rule_type=rule_type,
            category=category,
            created_by=created_by,
        )
        self._rules[rule_id] = rule
        self.logger.info(f"Created business rule: {name}")
        return rule_id

    def add_condition(
        self,
        rule_id: str,
        field_name: str,
        operator: OperatorType,
        value: Any,
        data_type: str = "string",
    ) -> str:
        """
        Add a condition to a rule.

        Args:
            rule_id: Rule to add condition to
            field_name: Field to evaluate
            operator: Comparison operator
            value: Value to compare against
            data_type: Data type of the field

        Returns:
            Condition ID
        """
        rule = self._rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")
        condition_id = str(uuid.uuid4())
        condition = RuleCondition(
            condition_id=condition_id,
            field_name=field_name,
            operator=operator,
            value=value,
            data_type=data_type,
        )
        rule.conditions.append(condition)
        rule.updated_at = datetime.now(timezone.utc)
        self.logger.info(
            f"Added condition to rule {rule_id}: {field_name} {operator.value} {value}"
        )
        return condition_id

    def add_action(
        self, rule_id: str, action_type: ActionType, parameters: Dict[str, Any] = None
    ) -> str:
        """
        Add an action to a rule.

        Args:
            rule_id: Rule to add action to
            action_type: Type of action
            parameters: Action parameters

        Returns:
            Action ID
        """
        rule = self._rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")
        action_id = str(uuid.uuid4())
        action = RuleAction(
            action_id=action_id, action_type=action_type, parameters=parameters or {}
        )
        rule.actions.append(action)
        rule.updated_at = datetime.now(timezone.utc)
        self.logger.info(f"Added action to rule {rule_id}: {action_type.value}")
        return action_id

    def execute_rules(
        self,
        data: Dict[str, Any],
        rule_category: str = None,
        rule_type: RuleType = None,
    ) -> List[RuleExecution]:
        """
        Execute rules against input data.

        Args:
            data: Input data to evaluate
            rule_category: Filter by rule category
            rule_type: Filter by rule type

        Returns:
            List of rule execution results
        """
        start_time = datetime.now(timezone.utc)
        executions = []
        applicable_rules = self._get_applicable_rules(rule_category, rule_type)
        applicable_rules.sort(key=lambda x: x.priority, reverse=True)
        for rule in applicable_rules:
            if not rule.enabled:
                continue
            execution_start = datetime.now(timezone.utc)
            try:
                conditions_met = self._evaluate_conditions(rule, data)
                executed_actions = []
                if conditions_met:
                    for action in rule.actions:
                        try:
                            self._execute_action(action, data)
                            executed_actions.append(action.action_id)
                        except Exception as e:
                            self.logger.error(
                                f"Error executing action {action.action_id}: {str(e)}"
                            )
                execution_time = (
                    datetime.now(timezone.utc) - execution_start
                ).total_seconds() * 1000
                execution = RuleExecution(
                    execution_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id,
                    executed_at=execution_start,
                    input_data=data.copy(),
                    conditions_met=conditions_met,
                    executed_actions=executed_actions,
                    execution_time_ms=execution_time,
                )
                executions.append(execution)
                self._rule_executions.append(execution)
                self._execution_stats[rule.rule_id].append(execution_time)
            except Exception as e:
                execution_time = (
                    datetime.now(timezone.utc) - execution_start
                ).total_seconds() * 1000
                execution = RuleExecution(
                    execution_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id,
                    executed_at=execution_start,
                    input_data=data.copy(),
                    conditions_met=False,
                    executed_actions=[],
                    execution_time_ms=execution_time,
                    error_message=str(e),
                )
                executions.append(execution)
                self._rule_executions.append(execution)
                self.logger.error(f"Error executing rule {rule.rule_id}: {str(e)}")
        total_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        self.logger.info(
            f"Executed {len(applicable_rules)} rules in {total_time:.2f}ms"
        )
        return executions

    def _get_applicable_rules(
        self, rule_category: str = None, rule_type: RuleType = None
    ) -> List[BusinessRule]:
        """Get rules applicable for execution."""
        rules = list(self._rules.values())
        if rule_category:
            rules = [r for r in rules if r.category == rule_category]
        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]
        return rules

    def _evaluate_conditions(self, rule: BusinessRule, data: Dict[str, Any]) -> bool:
        """Evaluate rule conditions against input data."""
        if not rule.conditions:
            return True
        condition_results = []
        for condition in rule.conditions:
            try:
                field_value = self._get_field_value(data, condition.field_name)
                condition_value = condition.value
                if condition.data_type == "number":
                    field_value = float(field_value) if field_value is not None else 0
                    if not isinstance(condition_value, (list, tuple)):
                        condition_value = float(condition_value)
                elif condition.data_type == "boolean":
                    field_value = bool(field_value)
                    condition_value = bool(condition_value)
                operator_func = self._operators.get(condition.operator)
                if operator_func:
                    result = operator_func(field_value, condition_value)
                    condition_results.append(result)
                else:
                    self.logger.warning(f"Unknown operator: {condition.operator}")
                    condition_results.append(False)
            except Exception as e:
                self.logger.error(
                    f"Error evaluating condition {condition.condition_id}: {str(e)}"
                )
                condition_results.append(False)
        if rule.condition_logic == "AND":
            return all(condition_results)
        elif rule.condition_logic == "OR":
            return any(condition_results)
        else:
            return self._evaluate_custom_logic(rule.condition_logic, condition_results)

    def _get_field_value(self, data: Dict[str, Any], field_name: str) -> object:
        """Get field value from data, supporting nested fields."""
        if "." in field_name:
            parts = field_name.split(".")
            value = data
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        else:
            return data.get(field_name)

    def _evaluate_custom_logic(
        self, logic_expression: str, condition_results: List[bool]
    ) -> bool:
        """Evaluate custom condition logic expression."""
        expression = logic_expression
        for i, result in enumerate(condition_results):
            expression = expression.replace(f"C{i}", str(result))
        try:
            return eval(expression.replace("AND", "and").replace("OR", "or"))
        except Exception:
            return False

    def _execute_action(self, action: RuleAction, data: Dict[str, Any]) -> object:
        """Execute a rule action."""
        handler = self._action_handlers.get(action.action_type)
        if handler:
            handler(action, data)
        else:
            self.logger.warning(f"No handler for action type: {action.action_type}")

    def _handle_set_value_action(
        self, action: RuleAction, data: Dict[str, Any]
    ) -> object:
        """Handle set value action."""
        field = action.parameters.get("field")
        value = action.parameters.get("value")
        if field:
            data[field] = value
            self.logger.info(f"Set {field} = {value}")

    def _handle_calculate_action(
        self, action: RuleAction, data: Dict[str, Any]
    ) -> object:
        """Handle calculation action."""
        formula = action.parameters.get("formula", "")
        result_field = action.parameters.get("result_field", "calculated_value")
        try:
            result = eval(formula, {"__builtins__": {}}, data)
            data[result_field] = result
            self.logger.info(f"Calculated {result_field} = {result}")
        except Exception as e:
            self.logger.error(f"Error in calculation: {str(e)}")

    def _handle_send_email_action(
        self, action: RuleAction, data: Dict[str, Any]
    ) -> object:
        """Handle send email action."""
        template = action.parameters.get("template", "")
        recipient = action.parameters.get("recipient", "")
        recipient_field = action.parameters.get("recipient_field", "")
        if recipient_field:
            recipient = data.get(recipient_field, recipient)
        self.logger.info(f"Sending email to {recipient} using template {template}")

    def _handle_create_task_action(
        self, action: RuleAction, data: Dict[str, Any]
    ) -> object:
        """Handle create task action."""
        task_type = action.parameters.get("task_type", "")
        assignee = action.parameters.get("assignee", "")
        action.parameters.get("description", "")
        self.logger.info(f"Creating task: {task_type} for {assignee}")

    def _handle_trigger_workflow_action(
        self, action: RuleAction, data: Dict[str, Any]
    ) -> object:
        """Handle trigger workflow action."""
        workflow_id = action.parameters.get("workflow_id", "")
        self.logger.info(f"Triggering workflow: {workflow_id}")

    def _handle_log_event_action(
        self, action: RuleAction, data: Dict[str, Any]
    ) -> object:
        """Handle log event action."""
        event_type = action.parameters.get("event_type", "")
        severity = action.parameters.get("severity", "info")
        message = action.parameters.get("message", "")
        self.logger.info(f"Logging event: {event_type} ({severity}) - {message}")

    def _handle_block_transaction_action(
        self, action: RuleAction, data: Dict[str, Any]
    ) -> object:
        """Handle block transaction action."""
        reason = action.parameters.get("reason", "Transaction blocked by rule")
        action.parameters.get("notify_customer", False)
        data["transaction_blocked"] = True
        data["block_reason"] = reason
        self.logger.warning(f"Transaction blocked: {reason}")

    def _handle_require_approval_action(
        self, action: RuleAction, data: Dict[str, Any]
    ) -> object:
        """Handle require approval action."""
        approver_role = action.parameters.get("approver_role", "")
        timeout_hours = action.parameters.get("timeout_hours", 24)
        data["requires_approval"] = True
        data["approver_role"] = approver_role
        data["approval_timeout"] = timeout_hours
        self.logger.info(f"Approval required from {approver_role}")

    def _handle_update_status_action(
        self, action: RuleAction, data: Dict[str, Any]
    ) -> object:
        """Handle update status action."""
        status_field = action.parameters.get("status_field", "status")
        new_status = action.parameters.get("new_status", "")
        data[status_field] = new_status
        self.logger.info(f"Updated {status_field} to {new_status}")

    def get_rule(self, rule_id: str) -> Optional[BusinessRule]:
        """Get business rule by ID."""
        return self._rules.get(rule_id)

    def list_rules(
        self,
        category: str = None,
        rule_type: RuleType = None,
        enabled_only: bool = False,
    ) -> List[BusinessRule]:
        """
        List business rules with optional filtering.

        Args:
            category: Filter by category
            rule_type: Filter by rule type
            enabled_only: Only return enabled rules

        Returns:
            List of business rules
        """
        rules = list(self._rules.values())
        if category:
            rules = [r for r in rules if r.category == category]
        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        rules.sort(key=lambda x: (-x.priority, x.name))
        return rules

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a business rule."""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = True
            rule.updated_at = datetime.now(timezone.utc)
            self.logger.info(f"Enabled rule: {rule_id}")
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a business rule."""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = False
            rule.updated_at = datetime.now(timezone.utc)
            self.logger.info(f"Disabled rule: {rule_id}")
            return True
        return False

    def test_rule(self, rule_id: str, test_data: Dict[str, Any]) -> RuleExecution:
        """
        Test a rule with sample data.

        Args:
            rule_id: Rule to test
            test_data: Test data

        Returns:
            Rule execution result
        """
        rule = self._rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")
        execution_start = datetime.now(timezone.utc)
        try:
            conditions_met = self._evaluate_conditions(rule, test_data)
            executed_actions = []
            if conditions_met:
                executed_actions = [action.action_id for action in rule.actions]
            execution_time = (
                datetime.now(timezone.utc) - execution_start
            ).total_seconds() * 1000
            return RuleExecution(
                execution_id=str(uuid.uuid4()),
                rule_id=rule_id,
                executed_at=execution_start,
                input_data=test_data.copy(),
                conditions_met=conditions_met,
                executed_actions=executed_actions,
                execution_time_ms=execution_time,
                metadata={"test_mode": True},
            )
        except Exception as e:
            execution_time = (
                datetime.now(timezone.utc) - execution_start
            ).total_seconds() * 1000
            return RuleExecution(
                execution_id=str(uuid.uuid4()),
                rule_id=rule_id,
                executed_at=execution_start,
                input_data=test_data.copy(),
                conditions_met=False,
                executed_actions=[],
                execution_time_ms=execution_time,
                error_message=str(e),
                metadata={"test_mode": True},
            )

    def create_from_template(
        self, template_id: str, name: str, description: str, created_by: str = None
    ) -> str:
        """Create rule from template."""
        template = self._rule_templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        rule_id = str(uuid.uuid4())
        rule = BusinessRule(
            rule_id=rule_id,
            name=name,
            description=description,
            rule_type=template.rule_type,
            conditions=copy.deepcopy(template.conditions),
            actions=copy.deepcopy(template.actions),
            condition_logic=template.condition_logic,
            priority=template.priority,
            category=template.category,
            tags=template.tags.copy(),
            created_by=created_by,
        )
        self._rules[rule_id] = rule
        self.logger.info(f"Created rule from template: {name}")
        return rule_id

    def get_rule_performance(self, rule_id: str) -> Dict[str, Any]:
        """Get performance statistics for a rule."""
        execution_times = self._execution_stats.get(rule_id, [])
        if not execution_times:
            return {"rule_id": rule_id, "executions": 0}
        return {
            "rule_id": rule_id,
            "executions": len(execution_times),
            "avg_execution_time_ms": sum(execution_times) / len(execution_times),
            "min_execution_time_ms": min(execution_times),
            "max_execution_time_ms": max(execution_times),
            "total_execution_time_ms": sum(execution_times),
        }

    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get rule engine statistics."""
        rule_categories = defaultdict(int)
        rule_types = defaultdict(int)
        enabled_rules = 0
        for rule in self._rules.values():
            rule_categories[rule.category] += 1
            rule_types[rule.rule_type.value] += 1
            if rule.enabled:
                enabled_rules += 1
        total_executions = len(self._rule_executions)
        successful_executions = len(
            [e for e in self._rule_executions if e.error_message is None]
        )
        return {
            "total_rules": len(self._rules),
            "enabled_rules": enabled_rules,
            "rule_categories": dict(rule_categories),
            "rule_types": dict(rule_types),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": (
                successful_executions / total_executions * 100
                if total_executions > 0
                else 0
            ),
            "registered_operators": len(self._operators),
            "registered_action_handlers": len(self._action_handlers),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
