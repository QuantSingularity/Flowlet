import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TransactionAnalytics(Base):
    __tablename__ = "transaction_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Transaction Details
    amount = Column(Numeric(precision=20, scale=8), nullable=False)
    currency = Column(String(3), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    payment_method = Column(String(50))
    merchant_category = Column(String(100))

    # Analytics Metrics
    risk_score = Column(Numeric(precision=5, scale=4))
    fraud_probability = Column(Numeric(precision=5, scale=4))
    customer_lifetime_value = Column(Numeric(precision=15, scale=2))
    transaction_velocity = Column(Integer)  # Transactions per hour

    # Geographic Data
    country_code = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))

    # Temporal Data
    transaction_date = Column(DateTime, nullable=False)
    hour_of_day = Column(Integer)
    day_of_week = Column(Integer)
    month = Column(Integer)
    quarter = Column(Integer)
    year = Column(Integer)

    # Behavioral Metrics
    is_first_transaction = Column(Boolean, default=False)
    days_since_last_transaction = Column(Integer)
    average_transaction_amount = Column(Numeric(precision=15, scale=2))

    # Compliance Flags
    requires_reporting = Column(Boolean, default=False)
    aml_flag = Column(Boolean, default=False)
    suspicious_activity = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index("idx_transaction_analytics_date", "transaction_date"),
        Index("idx_transaction_analytics_user", "user_id"),
        Index("idx_transaction_analytics_type", "transaction_type"),
        Index("idx_transaction_analytics_risk", "risk_score"),
        Index("idx_transaction_analytics_country", "country_code"),
        Index("idx_transaction_analytics_merchant", "merchant_category"),
    )


class CustomerAnalytics(Base):
    __tablename__ = "customer_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )

    # Customer Metrics
    total_transactions = Column(Integer, default=0)
    total_volume = Column(Numeric(precision=20, scale=2), default=0)
    average_transaction_size = Column(Numeric(precision=15, scale=2), default=0)

    # Behavioral Patterns
    preferred_payment_method = Column(String(50))
    most_active_hour = Column(Integer)
    most_active_day = Column(Integer)
    transaction_frequency = Column(String(20))  # daily, weekly, monthly

    # Risk Assessment
    overall_risk_score = Column(Numeric(precision=5, scale=4))
    kyc_completion_score = Column(Numeric(precision=3, scale=2))
    account_age_days = Column(Integer)

    # Engagement Metrics
    last_login = Column(DateTime)
    login_frequency = Column(Integer)  # Logins per month
    feature_usage = Column(JSONB)  # JSON object tracking feature usage

    # Financial Health
    average_balance = Column(Numeric(precision=15, scale=2))
    balance_volatility = Column(Numeric(precision=10, scale=4))
    credit_utilization = Column(Numeric(precision=5, scale=4))

    # Lifecycle Stage
    lifecycle_stage = Column(String(20))  # new, active, dormant, churned
    churn_probability = Column(Numeric(precision=5, scale=4))
    predicted_ltv = Column(Numeric(precision=15, scale=2))

    # Compliance Status
    kyc_status = Column(String(20))
    aml_status = Column(String(20))
    sanctions_check_date = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_customer_analytics_risk", "overall_risk_score"),
        Index("idx_customer_analytics_lifecycle", "lifecycle_stage"),
        Index("idx_customer_analytics_churn", "churn_probability"),
        Index("idx_customer_analytics_ltv", "predicted_ltv"),
    )


class BusinessMetrics(Base):
    __tablename__ = "business_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Metric Identification
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(
        String(50), nullable=False
    )  # revenue, risk, compliance, operational

    # Metric Values
    metric_value = Column(Numeric(precision=20, scale=8), nullable=False)
    previous_value = Column(Numeric(precision=20, scale=8))
    target_value = Column(Numeric(precision=20, scale=8))

    # Temporal Context
    measurement_date = Column(DateTime, nullable=False)
    period_type = Column(
        String(20), nullable=False
    )  # daily, weekly, monthly, quarterly

    # Metadata
    calculation_method = Column(Text)
    data_sources = Column(JSONB)
    confidence_level = Column(Numeric(precision=5, scale=4))

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_business_metrics_name_date", "metric_name", "measurement_date"),
        Index("idx_business_metrics_category", "metric_category"),
    )


class RegulatoryReport(Base):
    __tablename__ = "regulatory_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Report Identification
    report_type = Column(String(50), nullable=False)  # SAR, CTR, FBAR, etc.
    jurisdiction = Column(String(10), nullable=False)  # US, EU, UK, etc.
    reporting_period_start = Column(DateTime, nullable=False)
    reporting_period_end = Column(DateTime, nullable=False)

    # Report Content
    report_data = Column(JSONB, nullable=False)
    summary_statistics = Column(JSONB)

    # Submission Details
    submission_status = Column(
        String(20), default="draft"
    )  # draft, submitted, acknowledged
    submission_date = Column(DateTime)
    submission_reference = Column(String(100))

    # Compliance Officer Details
    prepared_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Audit Trail
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_regulatory_reports_type_jurisdiction", "report_type", "jurisdiction"
        ),
        Index(
            "idx_regulatory_reports_period",
            "reporting_period_start",
            "reporting_period_end",
        ),
        Index("idx_regulatory_reports_status", "submission_status"),
    )


class PerformanceMetrics(Base):
    __tablename__ = "performance_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Service Identification
    service_name = Column(String(100), nullable=False)
    endpoint = Column(String(200))

    # Performance Data
    response_time_ms = Column(Integer)
    throughput_rps = Column(Numeric(precision=10, scale=2))
    error_rate = Column(Numeric(precision=5, scale=4))
    cpu_usage = Column(Numeric(precision=5, scale=2))
    memory_usage = Column(Numeric(precision=10, scale=2))

    # Business Impact
    transaction_success_rate = Column(Numeric(precision=5, scale=4))
    revenue_impact = Column(Numeric(precision=15, scale=2))
    customer_satisfaction_score = Column(Numeric(precision=3, scale=2))

    # Temporal Data
    measurement_timestamp = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_performance_metrics_service_time",
            "service_name",
            "measurement_timestamp",
        ),
        Index("idx_performance_metrics_response_time", "response_time_ms"),
    )


class AlertConfiguration(Base):
    __tablename__ = "alert_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Alert Definition
    alert_name = Column(String(100), nullable=False)
    alert_type = Column(String(50), nullable=False)  # threshold, anomaly, pattern
    metric_name = Column(String(100), nullable=False)

    # Threshold Configuration
    threshold_value = Column(Numeric(precision=20, scale=8))
    comparison_operator = Column(String(10))  # >, <, >=, <=, ==, !=

    # Alert Behavior
    severity_level = Column(String(20), default="medium")  # low, medium, high, critical
    notification_channels = Column(JSONB)  # email, sms, webhook, etc.
    cooldown_period_minutes = Column(Integer, default=60)

    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_alert_configurations_metric", "metric_name"),
        Index("idx_alert_configurations_active", "is_active"),
    )
