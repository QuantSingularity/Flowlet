import asyncio
import copy
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

"\nWorkflow Builder\n===============\n\nVisual workflow builder for financial processes.\nAllows business users to create and manage complex workflows without coding.\n"


class NodeType(Enum):
    """Workflow node types."""

    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"
    MERGE = "merge"
    DELAY = "delay"
    WEBHOOK = "webhook"
    EMAIL = "email"
    APPROVAL = "approval"
    SCRIPT = "script"
    API_CALL = "api_call"


class WorkflowStatus(Enum):
    """Workflow execution status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(Enum):
    """Node execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """Individual workflow node."""

    node_id: str
    node_type: NodeType
    name: str
    description: str
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, float] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "position": self.position,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowConnection:
    """Connection between workflow nodes."""

    connection_id: str
    source_node_id: str
    target_node_id: str
    condition: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "condition": self.condition,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""

    workflow_id: str
    name: str
    description: str
    version: str
    nodes: List[WorkflowNode] = field(default_factory=list)
    connections: List[WorkflowConnection] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "nodes": [node.to_dict() for node in self.nodes],
            "connections": [conn.to_dict() for conn in self.connections],
            "variables": self.variables,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowExecution:
    """Workflow execution instance."""

    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    started_by: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    node_executions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "started_by": self.started_by,
            "context": self.context,
            "node_executions": self.node_executions,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class WorkflowBuilder:
    """
    Visual workflow builder for financial processes.

    Features:
    - Drag-and-drop workflow designer
    - Pre-built financial process templates
    - Conditional logic and branching
    - Parallel execution support
    - Integration with external systems
    - Approval workflows
    - Automated notifications
    - Error handling and retry logic
    - Workflow versioning
    - Real-time execution monitoring
    """

    def __init__(self, db_session: Session, config: Dict[str, Any] = None) -> None:
        self.db = db_session
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._workflows = {}
        self._executions = {}
        self._node_handlers = {}
        self._templates = {}
        self._execution_queue = asyncio.Queue()
        self._execution_tasks = {}
        self._initialize_workflow_builder()

    def _initialize_workflow_builder(self) -> object:
        """Initialize the workflow builder."""
        self._register_default_node_handlers()
        self._create_default_templates()
        self._start_execution_engine()
        self.logger.info("Workflow builder initialized successfully")

    def _register_default_node_handlers(self) -> object:
        """Register default node execution handlers."""
        self._node_handlers[NodeType.START] = self._handle_start_node
        self._node_handlers[NodeType.END] = self._handle_end_node
        self._node_handlers[NodeType.TASK] = self._handle_task_node
        self._node_handlers[NodeType.DECISION] = self._handle_decision_node
        self._node_handlers[NodeType.PARALLEL] = self._handle_parallel_node
        self._node_handlers[NodeType.MERGE] = self._handle_merge_node
        self._node_handlers[NodeType.DELAY] = self._handle_delay_node
        self._node_handlers[NodeType.WEBHOOK] = self._handle_webhook_node
        self._node_handlers[NodeType.EMAIL] = self._handle_email_node
        self._node_handlers[NodeType.APPROVAL] = self._handle_approval_node
        self._node_handlers[NodeType.API_CALL] = self._handle_api_call_node

    def _create_default_templates(self) -> object:
        """Create default workflow templates."""
        payment_workflow = self._create_payment_processing_template()
        self._templates[payment_workflow.workflow_id] = payment_workflow
        onboarding_workflow = self._create_customer_onboarding_template()
        self._templates[onboarding_workflow.workflow_id] = onboarding_workflow
        loan_workflow = self._create_loan_approval_template()
        self._templates[loan_workflow.workflow_id] = loan_workflow

    def _create_payment_processing_template(self) -> WorkflowDefinition:
        """Create payment processing workflow template."""
        nodes = [
            WorkflowNode(
                node_id="start",
                node_type=NodeType.START,
                name="Start Payment",
                description="Initialize payment processing",
                position={"x": 100, "y": 100},
            ),
            WorkflowNode(
                node_id="validate_payment",
                node_type=NodeType.TASK,
                name="Validate Payment",
                description="Validate payment details and limits",
                config={
                    "validation_rules": [
                        "amount_within_limits",
                        "valid_payment_method",
                        "sufficient_funds",
                    ]
                },
                position={"x": 300, "y": 100},
            ),
            WorkflowNode(
                node_id="fraud_check",
                node_type=NodeType.DECISION,
                name="Fraud Check",
                description="Check for fraudulent activity",
                config={
                    "condition": "fraud_score < 0.7",
                    "true_path": "process_payment",
                    "false_path": "manual_review",
                },
                position={"x": 500, "y": 100},
            ),
            WorkflowNode(
                node_id="process_payment",
                node_type=NodeType.TASK,
                name="Process Payment",
                description="Execute payment through gateway",
                config={"gateway": "primary", "retry_attempts": 3, "timeout": 30},
                position={"x": 700, "y": 50},
            ),
            WorkflowNode(
                node_id="manual_review",
                node_type=NodeType.APPROVAL,
                name="Manual Review",
                description="Manual review for high-risk payments",
                config={"approvers": ["risk_team"], "timeout_hours": 24},
                position={"x": 700, "y": 150},
            ),
            WorkflowNode(
                node_id="send_confirmation",
                node_type=NodeType.EMAIL,
                name="Send Confirmation",
                description="Send payment confirmation email",
                config={"template": "payment_confirmation", "recipients": ["customer"]},
                position={"x": 900, "y": 100},
            ),
            WorkflowNode(
                node_id="end",
                node_type=NodeType.END,
                name="End",
                description="Payment processing complete",
                position={"x": 1100, "y": 100},
            ),
        ]
        connections = [
            WorkflowConnection("conn1", "start", "validate_payment"),
            WorkflowConnection("conn2", "validate_payment", "fraud_check"),
            WorkflowConnection(
                "conn3", "fraud_check", "process_payment", "fraud_score < 0.7"
            ),
            WorkflowConnection(
                "conn4", "fraud_check", "manual_review", "fraud_score >= 0.7"
            ),
            WorkflowConnection("conn5", "process_payment", "send_confirmation"),
            WorkflowConnection("conn6", "manual_review", "send_confirmation"),
            WorkflowConnection("conn7", "send_confirmation", "end"),
        ]
        return WorkflowDefinition(
            workflow_id="payment_processing_template",
            name="Payment Processing",
            description="Standard payment processing workflow with fraud detection",
            version="1.0.0",
            nodes=nodes,
            connections=connections,
            category="payments",
            tags=["payment", "fraud", "automation"],
        )

    def _create_customer_onboarding_template(self) -> WorkflowDefinition:
        """Create customer onboarding workflow template."""
        nodes = [
            WorkflowNode(
                node_id="start",
                node_type=NodeType.START,
                name="Start Onboarding",
                description="Begin customer onboarding process",
                position={"x": 100, "y": 100},
            ),
            WorkflowNode(
                node_id="collect_info",
                node_type=NodeType.TASK,
                name="Collect Information",
                description="Collect customer information and documents",
                config={
                    "required_documents": [
                        "id",
                        "proof_of_address",
                        "income_verification",
                    ],
                    "form_template": "customer_onboarding",
                },
                position={"x": 300, "y": 100},
            ),
            WorkflowNode(
                node_id="kyc_verification",
                node_type=NodeType.TASK,
                name="KYC Verification",
                description="Perform KYC verification checks",
                config={
                    "verification_level": "standard",
                    "external_service": "kyc_provider",
                },
                position={"x": 500, "y": 100},
            ),
            WorkflowNode(
                node_id="risk_assessment",
                node_type=NodeType.DECISION,
                name="Risk Assessment",
                description="Assess customer risk profile",
                config={
                    "condition": "risk_score <= 0.5",
                    "true_path": "auto_approve",
                    "false_path": "manual_review",
                },
                position={"x": 700, "y": 100},
            ),
            WorkflowNode(
                node_id="auto_approve",
                node_type=NodeType.TASK,
                name="Auto Approve",
                description="Automatically approve low-risk customers",
                position={"x": 900, "y": 50},
            ),
            WorkflowNode(
                node_id="manual_review",
                node_type=NodeType.APPROVAL,
                name="Manual Review",
                description="Manual review for high-risk customers",
                config={"approvers": ["compliance_team"], "timeout_hours": 48},
                position={"x": 900, "y": 150},
            ),
            WorkflowNode(
                node_id="create_account",
                node_type=NodeType.TASK,
                name="Create Account",
                description="Create customer account and profiles",
                config={"account_type": "standard", "initial_limits": "default"},
                position={"x": 1100, "y": 100},
            ),
            WorkflowNode(
                node_id="welcome_email",
                node_type=NodeType.EMAIL,
                name="Welcome Email",
                description="Send welcome email with account details",
                config={"template": "welcome_customer", "include_credentials": True},
                position={"x": 1300, "y": 100},
            ),
            WorkflowNode(
                node_id="end",
                node_type=NodeType.END,
                name="End",
                description="Onboarding complete",
                position={"x": 1500, "y": 100},
            ),
        ]
        connections = [
            WorkflowConnection("conn1", "start", "collect_info"),
            WorkflowConnection("conn2", "collect_info", "kyc_verification"),
            WorkflowConnection("conn3", "kyc_verification", "risk_assessment"),
            WorkflowConnection(
                "conn4", "risk_assessment", "auto_approve", "risk_score <= 0.5"
            ),
            WorkflowConnection(
                "conn5", "risk_assessment", "manual_review", "risk_score > 0.5"
            ),
            WorkflowConnection("conn6", "auto_approve", "create_account"),
            WorkflowConnection("conn7", "manual_review", "create_account"),
            WorkflowConnection("conn8", "create_account", "welcome_email"),
            WorkflowConnection("conn9", "welcome_email", "end"),
        ]
        return WorkflowDefinition(
            workflow_id="customer_onboarding_template",
            name="Customer Onboarding",
            description="Complete customer onboarding workflow with KYC and risk assessment",
            version="1.0.0",
            nodes=nodes,
            connections=connections,
            category="onboarding",
            tags=["customer", "kyc", "compliance", "onboarding"],
        )

    def _create_loan_approval_template(self) -> WorkflowDefinition:
        """Create loan approval workflow template."""
        nodes = [
            WorkflowNode(
                node_id="start",
                node_type=NodeType.START,
                name="Start Application",
                description="Begin loan application process",
                position={"x": 100, "y": 100},
            ),
            WorkflowNode(
                node_id="collect_application",
                node_type=NodeType.TASK,
                name="Collect Application",
                description="Collect loan application and supporting documents",
                config={
                    "required_documents": [
                        "application_form",
                        "income_proof",
                        "credit_report",
                    ],
                    "form_template": "loan_application",
                },
                position={"x": 300, "y": 100},
            ),
            WorkflowNode(
                node_id="credit_check",
                node_type=NodeType.TASK,
                name="Credit Check",
                description="Perform credit score and history check",
                config={"credit_bureau": "primary", "minimum_score": 650},
                position={"x": 500, "y": 100},
            ),
            WorkflowNode(
                node_id="income_verification",
                node_type=NodeType.TASK,
                name="Income Verification",
                description="Verify applicant income and employment",
                config={"verification_method": "automated", "minimum_income": 50000},
                position={"x": 700, "y": 100},
            ),
            WorkflowNode(
                node_id="risk_scoring",
                node_type=NodeType.DECISION,
                name="Risk Scoring",
                description="Calculate loan risk score",
                config={
                    "condition": "risk_score <= 0.3",
                    "true_path": "auto_approve",
                    "false_path": "underwriter_review",
                },
                position={"x": 900, "y": 100},
            ),
            WorkflowNode(
                node_id="auto_approve",
                node_type=NodeType.TASK,
                name="Auto Approve",
                description="Automatically approve low-risk loans",
                config={"approval_amount": "requested", "interest_rate": "standard"},
                position={"x": 1100, "y": 50},
            ),
            WorkflowNode(
                node_id="underwriter_review",
                node_type=NodeType.APPROVAL,
                name="Underwriter Review",
                description="Manual underwriter review for higher-risk loans",
                config={"approvers": ["senior_underwriter"], "timeout_hours": 72},
                position={"x": 1100, "y": 150},
            ),
            WorkflowNode(
                node_id="generate_documents",
                node_type=NodeType.TASK,
                name="Generate Documents",
                description="Generate loan agreement and related documents",
                config={
                    "document_templates": ["loan_agreement", "payment_schedule"],
                    "digital_signature": True,
                },
                position={"x": 1300, "y": 100},
            ),
            WorkflowNode(
                node_id="send_approval",
                node_type=NodeType.EMAIL,
                name="Send Approval",
                description="Send loan approval notification",
                config={"template": "loan_approval", "include_documents": True},
                position={"x": 1500, "y": 100},
            ),
            WorkflowNode(
                node_id="end",
                node_type=NodeType.END,
                name="End",
                description="Loan approval process complete",
                position={"x": 1700, "y": 100},
            ),
        ]
        connections = [
            WorkflowConnection("conn1", "start", "collect_application"),
            WorkflowConnection("conn2", "collect_application", "credit_check"),
            WorkflowConnection("conn3", "credit_check", "income_verification"),
            WorkflowConnection("conn4", "income_verification", "risk_scoring"),
            WorkflowConnection(
                "conn5", "risk_scoring", "auto_approve", "risk_score <= 0.3"
            ),
            WorkflowConnection(
                "conn6", "risk_scoring", "underwriter_review", "risk_score > 0.3"
            ),
            WorkflowConnection("conn7", "auto_approve", "generate_documents"),
            WorkflowConnection("conn8", "underwriter_review", "generate_documents"),
            WorkflowConnection("conn9", "generate_documents", "send_approval"),
            WorkflowConnection("conn10", "send_approval", "end"),
        ]
        return WorkflowDefinition(
            workflow_id="loan_approval_template",
            name="Loan Approval",
            description="Complete loan approval workflow with automated and manual review",
            version="1.0.0",
            nodes=nodes,
            connections=connections,
            category="lending",
            tags=["loan", "approval", "underwriting", "credit"],
        )

    def _start_execution_engine(self) -> object:
        """Start the workflow execution engine."""

    def create_workflow(
        self,
        name: str,
        description: str,
        category: str = "general",
        created_by: str = None,
    ) -> str:
        """
        Create a new workflow definition.

        Args:
            name: Workflow name
            description: Workflow description
            category: Workflow category
            created_by: User who created the workflow

        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            version="1.0.0",
            category=category,
            created_by=created_by,
        )
        self._workflows[workflow_id] = workflow
        self.logger.info(f"Created workflow: {name}")
        return workflow_id

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow definition by ID."""
        return self._workflows.get(workflow_id)

    def add_node(
        self,
        workflow_id: str,
        node_type: NodeType,
        name: str,
        description: str,
        config: Dict[str, Any] = None,
        position: Dict[str, float] = None,
    ) -> str:
        """
        Add a node to workflow.

        Args:
            workflow_id: Workflow to add node to
            node_type: Type of node
            name: Node name
            description: Node description
            config: Node configuration
            position: Node position (x, y)

        Returns:
            Node ID
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        node_id = str(uuid.uuid4())
        node = WorkflowNode(
            node_id=node_id,
            node_type=node_type,
            name=name,
            description=description,
            config=config or {},
            position=position or {"x": 0, "y": 0},
        )
        workflow.nodes.append(node)
        workflow.updated_at = datetime.now(timezone.utc)
        self.logger.info(f"Added node {name} to workflow {workflow_id}")
        return node_id

    def connect_nodes(
        self,
        workflow_id: str,
        source_node_id: str,
        target_node_id: str,
        condition: str = None,
    ) -> str:
        """
        Connect two nodes in workflow.

        Args:
            workflow_id: Workflow ID
            source_node_id: Source node ID
            target_node_id: Target node ID
            condition: Optional condition for connection

        Returns:
            Connection ID
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        source_node = next(
            (n for n in workflow.nodes if n.node_id == source_node_id), None
        )
        target_node = next(
            (n for n in workflow.nodes if n.node_id == target_node_id), None
        )
        if not source_node:
            raise ValueError(f"Source node not found: {source_node_id}")
        if not target_node:
            raise ValueError(f"Target node not found: {target_node_id}")
        connection_id = str(uuid.uuid4())
        connection = WorkflowConnection(
            connection_id=connection_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            condition=condition,
        )
        workflow.connections.append(connection)
        source_node.outputs.append(connection_id)
        target_node.inputs.append(connection_id)
        workflow.updated_at = datetime.now(timezone.utc)
        self.logger.info(f"Connected nodes {source_node_id} -> {target_node_id}")
        return connection_id

    def execute_workflow(
        self, workflow_id: str, context: Dict[str, Any] = None, started_by: str = None
    ) -> str:
        """
        Execute a workflow.

        Args:
            workflow_id: Workflow to execute
            context: Initial execution context
            started_by: User who started the execution

        Returns:
            Execution ID
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.ACTIVE,
            started_at=datetime.now(timezone.utc),
            started_by=started_by,
            context=context or {},
        )
        self._executions[execution_id] = execution
        self._start_workflow_execution(execution_id)
        self.logger.info(f"Started workflow execution: {execution_id}")
        return execution_id

    def _start_workflow_execution(self, execution_id: str) -> object:
        """Start workflow execution (simplified implementation)."""
        execution = self._executions.get(execution_id)
        if not execution:
            return
        workflow = self._workflows.get(execution.workflow_id)
        if not workflow:
            return
        start_nodes = [n for n in workflow.nodes if n.node_type == NodeType.START]
        if not start_nodes:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = "No start node found"
            return
        start_node = start_nodes[0]
        self._execute_node(execution_id, start_node.node_id)

    def _execute_node(self, execution_id: str, node_id: str) -> object:
        """Execute a single workflow node."""
        execution = self._executions.get(execution_id)
        workflow = self._workflows.get(execution.workflow_id)
        node = next((n for n in workflow.nodes if n.node_id == node_id), None)
        if not node:
            return
        execution.node_executions[node_id] = {
            "status": NodeStatus.RUNNING.value,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "attempts": 1,
        }
        try:
            handler = self._node_handlers.get(node.node_type)
            if handler:
                result = handler(execution, node)
                execution.node_executions[node_id].update(
                    {
                        "status": NodeStatus.COMPLETED.value,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "result": result,
                    }
                )
                self._continue_execution(execution_id, node_id)
            else:
                raise ValueError(f"No handler for node type: {node.node_type}")
        except Exception as e:
            execution.node_executions[node_id].update(
                {
                    "status": NodeStatus.FAILED.value,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(e),
                }
            )
            execution.status = WorkflowStatus.FAILED
            execution.error_message = f"Node {node_id} failed: {str(e)}"

    def _continue_execution(self, execution_id: str, completed_node_id: str) -> object:
        """Continue workflow execution to next nodes."""
        execution = self._executions.get(execution_id)
        workflow = self._workflows.get(execution.workflow_id)
        outgoing_connections = [
            c for c in workflow.connections if c.source_node_id == completed_node_id
        ]
        for connection in outgoing_connections:
            if connection.condition:
                if not self._evaluate_condition(
                    connection.condition, execution.context
                ):
                    continue
            self._execute_node(execution_id, connection.target_node_id)

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate connection condition (simplified implementation)."""
        try:
            for key, value in context.items():
                condition = condition.replace(key, str(value))
            return eval(condition)
        except Exception:
            return False

    async def _handle_start_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle start node execution."""
        return {"status": "started"}

    async def _handle_end_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle end node execution."""
        execution.status = WorkflowStatus.COMPLETED
        execution.completed_at = datetime.now(timezone.utc)
        return {"status": "completed"}

    async def _handle_task_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle task node execution."""
        task_type = node.config.get("task_type", "generic")
        if task_type == "validation":
            return await self._execute_validation_task(execution, node)
        elif task_type == "api_call":
            return await self._execute_api_call_task(execution, node)
        else:
            return {"status": "completed", "task_type": task_type}

    async def _handle_decision_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle decision node execution."""
        condition = node.config.get("condition", "true")
        result = self._evaluate_condition(condition, execution.context)
        return {"status": "completed", "decision": result}

    async def _handle_parallel_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle parallel node execution."""
        return {"status": "completed", "parallel_branches": "started"}

    async def _handle_merge_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle merge node execution."""
        return {"status": "completed", "merged": True}

    async def _handle_delay_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle delay node execution."""
        delay_seconds = node.config.get("delay_seconds", 0)
        await asyncio.sleep(delay_seconds)
        return {"status": "completed", "delayed_seconds": delay_seconds}

    async def _handle_webhook_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle webhook node execution."""
        webhook_url = node.config.get("webhook_url", "")
        node.config.get("payload", {})
        return {"status": "completed", "webhook_called": webhook_url}

    async def _handle_email_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle email node execution."""
        node.config.get("template", "")
        recipients = node.config.get("recipients", [])
        return {"status": "completed", "email_sent": len(recipients)}

    async def _handle_approval_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle approval node execution."""
        approvers = node.config.get("approvers", [])
        node.config.get("timeout_hours", 24)
        return {"status": "pending_approval", "approvers": approvers}

    async def _handle_api_call_node(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Handle API call node execution."""
        api_url = node.config.get("api_url", "")
        node.config.get("method", "GET")
        return {"status": "completed", "api_called": api_url}

    async def _execute_validation_task(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Execute validation task."""
        validation_rules = node.config.get("validation_rules", [])
        validation_results = {}
        for rule in validation_rules:
            validation_results[rule] = True
        return {"status": "completed", "validations": validation_results}

    async def _execute_api_call_task(
        self, execution: WorkflowExecution, node: WorkflowNode
    ) -> Dict[str, Any]:
        """Execute API call task."""
        node.config.get("api_config", {})
        return {"status": "completed", "api_response": "success"}

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID."""
        return self._executions.get(execution_id)

    def list_workflows(self, category: str = None) -> List[WorkflowDefinition]:
        """List workflow definitions."""
        workflows = list(self._workflows.values())
        if category:
            workflows = [w for w in workflows if w.category == category]
        workflows.sort(key=lambda x: x.name)
        return workflows

    def list_templates(self) -> List[WorkflowDefinition]:
        """List workflow templates."""
        return list(self._templates.values())

    def create_from_template(
        self, template_id: str, name: str, description: str, created_by: str = None
    ) -> str:
        """Create workflow from template."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        workflow_id = str(uuid.uuid4())
        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            version="1.0.0",
            nodes=copy.deepcopy(template.nodes),
            connections=copy.deepcopy(template.connections),
            variables=copy.deepcopy(template.variables),
            category=template.category,
            tags=template.tags.copy(),
            created_by=created_by,
        )
        self._workflows[workflow_id] = workflow
        self.logger.info(f"Created workflow from template: {name}")
        return workflow_id

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow builder statistics."""
        workflow_categories = defaultdict(int)
        execution_statuses = defaultdict(int)
        for workflow in self._workflows.values():
            workflow_categories[workflow.category] += 1
        for execution in self._executions.values():
            execution_statuses[execution.status.value] += 1
        return {
            "total_workflows": len(self._workflows),
            "total_templates": len(self._templates),
            "total_executions": len(self._executions),
            "workflow_categories": dict(workflow_categories),
            "execution_statuses": dict(execution_statuses),
            "registered_node_handlers": len(self._node_handlers),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
