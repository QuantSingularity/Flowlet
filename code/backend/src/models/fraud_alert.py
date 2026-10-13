import json
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text

from .database import Base, db


class FraudAlertStatus(PyEnum):
    PENDING = "pending"
    INVESTIGATING = "investigating"
    REVIEWED = "reviewed"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    transaction_id = Column(String(64), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False)
    status = Column(db.Enum(FraudAlertStatus), default=FraudAlertStatus.PENDING)
    description = Column(Text)
    risk_score = Column(db.Float, default=0.0)
    risk_level = Column(String(16))
    action = Column(String(16))
    model_version = Column(String(64))
    ml_alert_id = Column(String(36), index=True)
    details = Column(Text)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(36), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_fraud_alert_status_created", "status", "created_at"),
        Index("idx_fraud_alert_user_created", "user_id", "created_at"),
    )

    def set_details(self, payload: dict) -> None:
        self.details = json.dumps(payload, default=str)

    def get_details(self) -> dict:
        if not self.details:
            return {}
        try:
            return json.loads(self.details)
        except ValueError:
            return {}

    def to_dict(self, include_details: bool = False) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "transaction_id": self.transaction_id,
            "alert_type": self.alert_type,
            "status": self.status.value if self.status else None,
            "description": self.description,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "action": self.action,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
        }
        if include_details:
            data["details"] = self.get_details()
        return data
