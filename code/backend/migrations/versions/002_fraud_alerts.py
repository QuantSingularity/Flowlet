"""Fraud alerts table with ML scoring columns

Revision ID: 002_fraud_alerts
Revises: 001_initial
Create Date: 2026-10-12 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "002_fraud_alerts"
down_revision = "001_initial"
branch_labels = None
depends_on = None

STATUS_VALUES = (
    "PENDING",
    "INVESTIGATING",
    "REVIEWED",
    "CONFIRMED",
    "FALSE_POSITIVE",
    "DISMISSED",
    "RESOLVED",
)


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "fraud_alerts" not in inspector.get_table_names():
        op.create_table(
            "fraud_alerts",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id")),
            sa.Column("transaction_id", sa.String(64)),
            sa.Column("alert_type", sa.String(50), nullable=False),
            sa.Column("status", sa.Enum(*STATUS_VALUES, name="fraudalertstatus")),
            sa.Column("description", sa.Text()),
            sa.Column("risk_score", sa.Float(), server_default="0"),
            sa.Column("risk_level", sa.String(16)),
            sa.Column("action", sa.String(16)),
            sa.Column("model_version", sa.String(64)),
            sa.Column("ml_alert_id", sa.String(36)),
            sa.Column("details", sa.Text()),
            sa.Column("resolved_at", sa.DateTime(timezone=True)),
            sa.Column("resolved_by", sa.String(36)),
            sa.Column("resolution_notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True)),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        )
        op.create_index("ix_fraud_alerts_user_id", "fraud_alerts", ["user_id"])
        op.create_index(
            "ix_fraud_alerts_transaction_id", "fraud_alerts", ["transaction_id"]
        )
        op.create_index("ix_fraud_alerts_ml_alert_id", "fraud_alerts", ["ml_alert_id"])
        op.create_index(
            "idx_fraud_alert_status_created", "fraud_alerts", ["status", "created_at"]
        )
        op.create_index(
            "idx_fraud_alert_user_created", "fraud_alerts", ["user_id", "created_at"]
        )
        return
    existing = {column["name"] for column in inspector.get_columns("fraud_alerts")}
    additions = [
        ("risk_level", sa.String(16)),
        ("action", sa.String(16)),
        ("model_version", sa.String(64)),
        ("ml_alert_id", sa.String(36)),
        ("details", sa.Text()),
        ("resolved_at", sa.DateTime(timezone=True)),
        ("resolved_by", sa.String(36)),
        ("resolution_notes", sa.Text()),
    ]
    for name, column_type in additions:
        if name not in existing:
            op.add_column("fraud_alerts", sa.Column(name, column_type))


def downgrade():
    op.drop_table("fraud_alerts")
