import json
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum as PyEnum
from typing import Any

import flask
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base, db


class AuditEventType(PyEnum):
    """Types of audit events"""

    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTRATION = "user_registration"
    USER_MODIFICATION = "user_modification"
    USER_DELETION = "user_deletion"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_CREATION = "account_creation"
    ACCOUNT_MODIFICATION = "account_modification"
    ACCOUNT_DELETION = "account_deletion"
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_MODIFIED = "transaction_modified"
    TRANSACTION_COMPLETED = "transaction_completed"
    FINANCIAL_TRANSACTION = "financial_transaction"
    CARD_CREATED = "card_created"
    CARD_BLOCKED = "card_blocked"
    CARD_UNBLOCKED = "card_unblocked"
    PERMISSION_CHANGE = "permission_change"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    DATA_UPLOAD = "data_upload"
    SECURITY_ALERT = "security_alert"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"
    COMPLIANCE_EVENT = "compliance_event"
    COMPLIANCE_REPORT = "compliance_report"
    SYSTEM_ERROR = "system_error"
    SYSTEM_EVENT = "system_event"
    API_REQUEST = "api_request"
    ADMIN_ACTION = "admin_action"
    MFA_CHANGE = "mfa_change"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    KYC_UPDATE = "kyc_update"


class AuditSeverity(PyEnum):
    """Severity levels for audit events"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base):
    """Comprehensive audit logging for compliance and security monitoring"""

    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(db.Enum(AuditEventType), nullable=False, index=True)
    severity = Column(db.Enum(AuditSeverity), default=AuditSeverity.LOW, nullable=False)
    description = Column(String(500), nullable=False)
    details = Column(Text)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255))
    user_email = Column(String(255), nullable=True)
    endpoint = Column(String(200))
    method = Column(String(10))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(36), nullable=True, index=True)
    status_code = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(String(500))
    status = Column(String(20), nullable=False, default="success")
    retention_period_days = Column(Integer, default=2555)
    is_pii_related = Column(Boolean, default=False)
    is_financial_data = Column(Boolean, default=False)
    risk_level = Column(Integer, nullable=False, default=1)
    is_sensitive = Column(Boolean, nullable=False, default=False)
    country_code = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    user = relationship("User", backref="audit_logs")
    __table_args__ = (
        Index("idx_audit_event_type", "event_type"),
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_created_at", "created_at"),
    )

    def set_details(self, details_dict: Any) -> None:
        """Set details as JSON string"""
        if details_dict:
            self.details = json.dumps(details_dict, default=str)

    def get_details(self) -> "flask.Response":
        """Get details as dictionary"""
        if self.details:
            try:
                return json.loads(self.details)
            except json.JSONDecodeError:
                return {}
        return {}

    def is_expired(self) -> bool:
        """Check if audit log has exceeded retention period"""
        expiry_date = self.created_at + timedelta(days=self.retention_period_days)
        return datetime.now(timezone.utc) > expiry_date

    def to_dict(self) -> dict:
        """Convert audit log to dictionary for API responses"""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "details": self.get_details(),
            "user_id": self.user_id,
            "user_email": self.user_email,
            "endpoint": self.endpoint,
            "method": self.method,
            "ip_address": self.ip_address,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "status_code": self.status_code,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<AuditLog {self.event_type.value}: {self.description}>"
