"""Initial schema - users, accounts, transactions, cards, kyc records

Revision ID: 001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("phone_number", sa.String(20)),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("role", sa.String(50), nullable=False, server_default="customer"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("kyc_status", sa.String(50), server_default="not_started"),
        sa.Column("mfa_enabled", sa.Boolean(), server_default="0"),
        sa.Column("is_email_verified", sa.Boolean(), server_default="0"),
        sa.Column("last_login_at", sa.DateTime()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    # Accounts
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("account_number", sa.String(20), nullable=False, unique=True),
        sa.Column("account_type", sa.String(50), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("balance", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column(
            "available_balance", sa.Numeric(18, 2), nullable=False, server_default="0"
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("daily_limit", sa.Numeric(18, 2), server_default="10000"),
        sa.Column("monthly_limit", sa.Numeric(18, 2), server_default="50000"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    # Transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "account_id", sa.String(36), sa.ForeignKey("accounts.id"), nullable=False
        ),
        sa.Column("from_account_id", sa.String(36)),
        sa.Column("to_account_id", sa.String(36)),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("description", sa.Text()),
        sa.Column("reference", sa.String(100)),
        sa.Column("metadata_json", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    # Cards
    op.create_table(
        "cards",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "account_id", sa.String(36), sa.ForeignKey("accounts.id"), nullable=False
        ),
        sa.Column("card_number_masked", sa.String(20), nullable=False),
        sa.Column("card_number_encrypted", sa.Text()),
        sa.Column("card_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="inactive"),
        sa.Column("expiry_month", sa.Integer(), nullable=False),
        sa.Column("expiry_year", sa.Integer(), nullable=False),
        sa.Column("cardholder_name", sa.String(200), nullable=False),
        sa.Column("daily_limit", sa.Numeric(18, 2), server_default="2000"),
        sa.Column("monthly_limit", sa.Numeric(18, 2), server_default="10000"),
        sa.Column("contactless_enabled", sa.Boolean(), server_default="1"),
        sa.Column("online_enabled", sa.Boolean(), server_default="1"),
        sa.Column("international_enabled", sa.Boolean(), server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    # Indexes
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_created_at", "transactions", ["created_at"])
    op.create_index("ix_cards_account_id", "cards", ["account_id"])


def downgrade():
    op.drop_table("cards")
    op.drop_table("transactions")
    op.drop_table("accounts")
    op.drop_table("users")
