import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from .data_models import CustomerAnalytics, TransactionAnalytics


class DataSourceType(Enum):
    """Types of data sources for ETL."""

    TRANSACTIONAL_DB = "transactional_db"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"
    STREAMING = "streaming"


class ETLJobStatus(Enum):
    """Status of ETL jobs."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ETLJob:
    """ETL job configuration and status."""

    id: str
    name: str
    source_type: DataSourceType
    source_config: Dict[str, Any]
    target_table: str
    schedule: str
    status: ETLJobStatus = ETLJobStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> object:
        if self.last_run is None:
            self.last_run = datetime.now(timezone.utc)


@dataclass
class DataQualityRule:
    """Data quality validation rule."""

    name: str
    description: str
    table_name: str
    column_name: str
    rule_type: str
    parameters: Dict[str, Any]
    severity: str = "error"


class DataWarehouse:
    """
    Enterprise data warehouse for financial analytics.

    Features:
    - ETL pipeline management
    - Data quality validation
    - Dimensional modeling
    - Query optimization
    - Data lineage tracking
    - Automated data refresh
    """

    def __init__(
        self, db_session: Session, warehouse_config: Dict[str, Any] = None
    ) -> None:
        self.db = db_session
        self.config = warehouse_config or {}
        self.logger = logging.getLogger(__name__)
        self._etl_jobs = {}
        self._data_quality_rules = []
        self._initialize_warehouse()

    def _initialize_warehouse(self) -> object:
        """Initialize the data warehouse with default configurations."""
        self._setup_default_etl_jobs()
        self._setup_data_quality_rules()
        self.logger.info("Data warehouse initialized successfully")

    def _setup_default_etl_jobs(self) -> object:
        """Set up default ETL jobs for common data sources."""
        transaction_etl = ETLJob(
            id="transaction_analytics_etl",
            name="Transaction Analytics ETL",
            source_type=DataSourceType.TRANSACTIONAL_DB,
            source_config={
                "source_table": "transactions",
                "incremental_column": "created_at",
                "batch_size": 10000,
            },
            target_table="transaction_analytics",
            schedule="0 */15 * * * *",
        )
        self._etl_jobs[transaction_etl.id] = transaction_etl
        customer_etl = ETLJob(
            id="customer_analytics_etl",
            name="Customer Analytics ETL",
            source_type=DataSourceType.TRANSACTIONAL_DB,
            source_config={
                "source_table": "users",
                "incremental_column": "updated_at",
                "batch_size": 5000,
            },
            target_table="customer_analytics",
            schedule="0 0 */6 * * *",
        )
        self._etl_jobs[customer_etl.id] = customer_etl
        performance_etl = ETLJob(
            id="performance_metrics_etl",
            name="Performance Metrics ETL",
            source_type=DataSourceType.EXTERNAL_API,
            source_config={
                "api_endpoint": "/metrics/performance",
                "auth_method": "bearer_token",
                "batch_size": 1000,
            },
            target_table="performance_metrics",
            schedule="0 */5 * * * *",
        )
        self._etl_jobs[performance_etl.id] = performance_etl

    def _setup_data_quality_rules(self) -> object:
        """Set up data quality validation rules."""
        self._data_quality_rules.extend(
            [
                DataQualityRule(
                    name="transaction_amount_not_null",
                    description="Transaction amount must not be null",
                    table_name="transaction_analytics",
                    column_name="amount",
                    rule_type="not_null",
                    parameters={},
                ),
                DataQualityRule(
                    name="transaction_amount_positive",
                    description="Transaction amount must be positive",
                    table_name="transaction_analytics",
                    column_name="amount",
                    rule_type="range",
                    parameters={"min_value": 0},
                ),
                DataQualityRule(
                    name="currency_code_valid",
                    description="Currency code must be valid ISO 4217",
                    table_name="transaction_analytics",
                    column_name="currency",
                    rule_type="pattern",
                    parameters={"pattern": "^[A-Z]{3}$"},
                ),
                DataQualityRule(
                    name="risk_score_range",
                    description="Risk score must be between 0 and 1",
                    table_name="transaction_analytics",
                    column_name="risk_score",
                    rule_type="range",
                    parameters={"min_value": 0, "max_value": 1},
                ),
            ]
        )
        self._data_quality_rules.extend(
            [
                DataQualityRule(
                    name="user_id_unique",
                    description="User ID must be unique",
                    table_name="customer_analytics",
                    column_name="user_id",
                    rule_type="unique",
                    parameters={},
                ),
                DataQualityRule(
                    name="ltv_non_negative",
                    description="Customer LTV must be non-negative",
                    table_name="customer_analytics",
                    column_name="predicted_ltv",
                    rule_type="range",
                    parameters={"min_value": 0},
                ),
                DataQualityRule(
                    name="churn_probability_range",
                    description="Churn probability must be between 0 and 1",
                    table_name="customer_analytics",
                    column_name="churn_probability",
                    rule_type="range",
                    parameters={"min_value": 0, "max_value": 1},
                ),
            ]
        )

    async def run_etl_job(self, job_id: str) -> Dict[str, Any]:
        """
        Run a specific ETL job.

        Args:
            job_id: ID of the ETL job to run

        Returns:
            Dictionary containing job execution results
        """
        if job_id not in self._etl_jobs:
            raise ValueError(f"ETL job {job_id} not found")
        job = self._etl_jobs[job_id]
        try:
            self.logger.info(f"Starting ETL job: {job.name}")
            job.status = ETLJobStatus.RUNNING
            job.last_run = datetime.now(timezone.utc)
            if job.source_type == DataSourceType.TRANSACTIONAL_DB:
                result = await self._run_transactional_etl(job)
            elif job.source_type == DataSourceType.EXTERNAL_API:
                result = await self._run_api_etl(job)
            elif job.source_type == DataSourceType.FILE_SYSTEM:
                result = await self._run_file_etl(job)
            elif job.source_type == DataSourceType.STREAMING:
                result = await self._run_streaming_etl(job)
            else:
                raise ValueError(f"Unsupported source type: {job.source_type}")
            job.status = ETLJobStatus.COMPLETED
            job.error_message = None
            quality_results = await self._validate_data_quality(job.target_table)
            self.logger.info(f"ETL job {job.name} completed successfully")
            return {
                "job_id": job_id,
                "status": "completed",
                "records_processed": result.get("records_processed", 0),
                "execution_time": result.get("execution_time", 0),
                "data_quality": quality_results,
            }
        except Exception as e:
            job.status = ETLJobStatus.FAILED
            job.error_message = str(e)
            self.logger.error(f"ETL job {job.name} failed: {str(e)}")
            return {"job_id": job_id, "status": "failed", "error": str(e)}

    async def _run_transactional_etl(self, job: ETLJob) -> Dict[str, Any]:
        """Run ETL for transactional database sources."""
        start_time = datetime.now(timezone.utc)
        source_config = job.source_config
        source_config.get("incremental_column", "created_at")
        batch_size = source_config.get("batch_size", 10000)
        last_processed = self._get_last_processed_timestamp(job.id)
        if job.target_table == "transaction_analytics":
            records_processed = await self._extract_transaction_analytics(
                last_processed, batch_size
            )
        elif job.target_table == "customer_analytics":
            records_processed = await self._extract_customer_analytics(
                last_processed, batch_size
            )
        else:
            records_processed = 0
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        self._update_last_processed_timestamp(job.id, datetime.now(timezone.utc))
        return {
            "records_processed": records_processed,
            "execution_time": execution_time,
        }

    async def _extract_transaction_analytics(
        self, last_processed: datetime, batch_size: int
    ) -> int:
        """Extract and transform transaction data for analytics."""
        query = text(
            "\n            SELECT\n                t.id as transaction_id,\n                t.user_id,\n                t.amount,\n                t.currency,\n                t.transaction_type,\n                t.payment_method,\n                t.merchant_category,\n                t.country_code,\n                t.created_at as transaction_date,\n                EXTRACT(HOUR FROM t.created_at) as hour_of_day,\n                EXTRACT(DOW FROM t.created_at) as day_of_week,\n                EXTRACT(MONTH FROM t.created_at) as month,\n                EXTRACT(QUARTER FROM t.created_at) as quarter,\n                EXTRACT(YEAR FROM t.created_at) as year\n            FROM transactions t\n            WHERE t.created_at > :last_processed\n            ORDER BY t.created_at\n            LIMIT :batch_size\n        "
        )
        result = self.db.execute(
            query, {"last_processed": last_processed, "batch_size": batch_size}
        )
        transactions = result.fetchall()
        records_processed = 0
        for transaction in transactions:
            risk_score = self._calculate_risk_score(transaction)
            fraud_probability = self._calculate_fraud_probability(transaction)
            is_first_transaction = self._is_first_transaction(transaction.user_id)
            days_since_last = self._calculate_days_since_last_transaction(
                transaction.user_id
            )
            analytics_record = TransactionAnalytics(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                amount=transaction.amount,
                currency=transaction.currency,
                transaction_type=transaction.transaction_type,
                payment_method=transaction.payment_method,
                merchant_category=transaction.merchant_category,
                risk_score=risk_score,
                fraud_probability=fraud_probability,
                country_code=transaction.country_code,
                transaction_date=transaction.transaction_date,
                hour_of_day=transaction.hour_of_day,
                day_of_week=transaction.day_of_week,
                month=transaction.month,
                quarter=transaction.quarter,
                year=transaction.year,
                is_first_transaction=is_first_transaction,
                days_since_last_transaction=days_since_last,
                requires_reporting=transaction.amount > 10000,
                aml_flag=risk_score > 0.8,
                suspicious_activity=fraud_probability > 0.7,
            )
            self.db.add(analytics_record)
            records_processed += 1
        self.db.commit()
        return records_processed

    async def _extract_customer_analytics(
        self, last_processed: datetime, batch_size: int
    ) -> int:
        """Extract and transform customer data for analytics."""
        query = text(
            "\n            SELECT\n                u.id as user_id,\n                u.created_at,\n                u.updated_at,\n                u.kyc_status,\n                u.last_login,\n                COUNT(t.id) as total_transactions,\n                COALESCE(SUM(t.amount), 0) as total_volume,\n                COALESCE(AVG(t.amount), 0) as average_transaction_size\n            FROM users u\n            LEFT JOIN transactions t ON u.id = t.user_id\n            WHERE u.updated_at > :last_processed\n            GROUP BY u.id, u.created_at, u.updated_at, u.kyc_status, u.last_login\n            ORDER BY u.updated_at\n            LIMIT :batch_size\n        "
        )
        result = self.db.execute(
            query, {"last_processed": last_processed, "batch_size": batch_size}
        )
        users = result.fetchall()
        records_processed = 0
        for user in users:
            account_age_days = (datetime.now(timezone.utc) - user.created_at).days
            overall_risk_score = self._calculate_customer_risk_score(user)
            churn_probability = self._calculate_churn_probability(user)
            predicted_ltv = self._calculate_predicted_ltv(user)
            lifecycle_stage = self._determine_lifecycle_stage(user)
            existing_record = (
                self.db.query(CustomerAnalytics)
                .filter(CustomerAnalytics.user_id == user.user_id)
                .first()
            )
            if existing_record:
                existing_record.total_transactions = user.total_transactions
                existing_record.total_volume = user.total_volume
                existing_record.average_transaction_size = user.average_transaction_size
                existing_record.overall_risk_score = overall_risk_score
                existing_record.account_age_days = account_age_days
                existing_record.churn_probability = churn_probability
                existing_record.predicted_ltv = predicted_ltv
                existing_record.lifecycle_stage = lifecycle_stage
                existing_record.last_login = user.last_login
                existing_record.kyc_status = user.kyc_status
                existing_record.updated_at = datetime.now(timezone.utc)
            else:
                analytics_record = CustomerAnalytics(
                    user_id=user.user_id,
                    total_transactions=user.total_transactions,
                    total_volume=user.total_volume,
                    average_transaction_size=user.average_transaction_size,
                    overall_risk_score=overall_risk_score,
                    account_age_days=account_age_days,
                    churn_probability=churn_probability,
                    predicted_ltv=predicted_ltv,
                    lifecycle_stage=lifecycle_stage,
                    last_login=user.last_login,
                    kyc_status=user.kyc_status,
                )
                self.db.add(analytics_record)
            records_processed += 1
        self.db.commit()
        return records_processed

    async def _run_api_etl(self, job: ETLJob) -> Dict[str, Any]:
        """Run ETL for external API sources."""
        return {"records_processed": 0, "execution_time": 0}

    async def _run_file_etl(self, job: ETLJob) -> Dict[str, Any]:
        """Run ETL for file system sources."""
        return {"records_processed": 0, "execution_time": 0}

    async def _run_streaming_etl(self, job: ETLJob) -> Dict[str, Any]:
        """Run ETL for streaming sources."""
        return {"records_processed": 0, "execution_time": 0}

    async def _validate_data_quality(self, table_name: str) -> Dict[str, Any]:
        """Validate data quality for a specific table."""
        quality_results = {
            "table_name": table_name,
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "rules_passed": 0,
            "rules_failed": 0,
            "warnings": 0,
            "errors": [],
            "warnings_list": [],
        }
        table_rules = [
            rule for rule in self._data_quality_rules if rule.table_name == table_name
        ]
        for rule in table_rules:
            try:
                is_valid = await self._validate_rule(rule)
                if is_valid:
                    quality_results["rules_passed"] += 1
                else:
                    quality_results["rules_failed"] += 1
                    if rule.severity == "error":
                        quality_results["errors"].append(
                            {
                                "rule_name": rule.name,
                                "description": rule.description,
                                "column": rule.column_name,
                            }
                        )
                    elif rule.severity == "warning":
                        quality_results["warnings"] += 1
                        quality_results["warnings_list"].append(
                            {
                                "rule_name": rule.name,
                                "description": rule.description,
                                "column": rule.column_name,
                            }
                        )
            except Exception as e:
                self.logger.error(f"Error validating rule {rule.name}: {str(e)}")
                quality_results["errors"].append(
                    {"rule_name": rule.name, "error": str(e)}
                )
        return quality_results

    async def _validate_rule(self, rule: DataQualityRule) -> bool:
        """Validate a specific data quality rule."""
        if rule.rule_type == "not_null":
            query = text(
                f"\n                SELECT COUNT(*) as null_count\n                FROM {rule.table_name}\n                WHERE {rule.column_name} IS NULL\n            "
            )
            result = self.db.execute(query).fetchone()
            return result.null_count == 0
        elif rule.rule_type == "unique":
            query = text(
                f"\n                SELECT COUNT(*) as total_count,\n                       COUNT(DISTINCT {rule.column_name}) as unique_count\n                FROM {rule.table_name}\n                WHERE {rule.column_name} IS NOT NULL\n            "
            )
            result = self.db.execute(query).fetchone()
            return result.total_count == result.unique_count
        elif rule.rule_type == "range":
            conditions = []
            if "min_value" in rule.parameters:
                conditions.append(
                    f"{rule.column_name} >= {rule.parameters['min_value']}"
                )
            if "max_value" in rule.parameters:
                conditions.append(
                    f"{rule.column_name} <= {rule.parameters['max_value']}"
                )
            if conditions:
                where_clause = " AND ".join(conditions)
                query = text(
                    f"\n                    SELECT COUNT(*) as invalid_count\n                    FROM {rule.table_name}\n                    WHERE {rule.column_name} IS NOT NULL\n                    AND NOT ({where_clause})\n                "
                )
                result = self.db.execute(query).fetchone()
                return result.invalid_count == 0
        elif rule.rule_type == "pattern":
            pattern = rule.parameters.get("pattern", "")
            query = text(
                f"\n                SELECT COUNT(*) as invalid_count\n                FROM {rule.table_name}\n                WHERE {rule.column_name} IS NOT NULL\n                AND {rule.column_name} !~ :pattern\n            "
            )
            result = self.db.execute(query, {"pattern": pattern}).fetchone()
            return result.invalid_count == 0
        return True

    def _calculate_risk_score(self, transaction: Any) -> float:
        """Calculate risk score for a transaction (placeholder implementation)."""
        risk_factors = 0
        if transaction.amount > 10000:
            risk_factors += 0.3
        if transaction.country_code and transaction.country_code not in ["US", "CA"]:
            risk_factors += 0.2
        if transaction.hour_of_day < 6 or transaction.hour_of_day > 22:
            risk_factors += 0.1
        if transaction.day_of_week in [0, 6]:
            risk_factors += 0.1
        return min(risk_factors, 1.0)

    def _calculate_fraud_probability(self, transaction: Any) -> float:
        """Calculate fraud probability for a transaction."""
        base_probability = 0.01
        if transaction.amount > 5000:
            base_probability *= 2
        if transaction.payment_method == "card":
            base_probability *= 1.5
        return min(base_probability, 1.0)

    def _is_first_transaction(self, user_id: Any) -> bool:
        """Check if this is the user's first transaction."""
        count = (
            self.db.query(func.count(TransactionAnalytics.id))
            .filter(TransactionAnalytics.user_id == user_id)
            .scalar()
        )
        return count == 0

    def _calculate_days_since_last_transaction(self, user_id: Any) -> Optional[int]:
        """Calculate days since user's last transaction."""
        last_transaction = (
            self.db.query(TransactionAnalytics)
            .filter(TransactionAnalytics.user_id == user_id)
            .order_by(TransactionAnalytics.transaction_date.desc())
            .first()
        )
        if last_transaction:
            return (datetime.now(timezone.utc) - last_transaction.transaction_date).days
        return None

    def _calculate_customer_risk_score(self, user: Any) -> float:
        """Calculate overall risk score for a customer."""
        risk_score = 0.1
        account_age_days = (datetime.now(timezone.utc) - user.created_at).days
        if account_age_days < 30:
            risk_score += 0.3
        elif account_age_days < 90:
            risk_score += 0.1
        if user.total_volume > 100000:
            risk_score += 0.2
        if user.kyc_status != "completed":
            risk_score += 0.4
        return min(risk_score, 1.0)

    def _calculate_churn_probability(self, user: Any) -> float:
        """Calculate churn probability for a customer."""
        base_churn = 0.1
        if user.last_login:
            days_since_login = (datetime.now(timezone.utc) - user.last_login).days
            if days_since_login > 30:
                base_churn += 0.3
            elif days_since_login > 7:
                base_churn += 0.1
        if user.total_transactions == 0:
            base_churn += 0.5
        elif user.total_transactions < 5:
            base_churn += 0.2
        return min(base_churn, 1.0)

    def _calculate_predicted_ltv(self, user: Any) -> float:
        """Calculate predicted lifetime value for a customer."""
        if user.total_transactions == 0:
            return 0.0
        avg_transaction = user.average_transaction_size
        estimated_lifetime_transactions = user.total_transactions * 10
        retention_probability = 1 - self._calculate_churn_probability(user)
        return float(
            avg_transaction
            * estimated_lifetime_transactions
            * retention_probability
            * 0.029
        )

    def _determine_lifecycle_stage(self, user: Any) -> str:
        """Determine customer lifecycle stage."""
        account_age_days = (datetime.now(timezone.utc) - user.created_at).days
        if user.total_transactions == 0:
            return "new"
        elif account_age_days < 30:
            return "new"
        elif (
            user.last_login and (datetime.now(timezone.utc) - user.last_login).days > 90
        ):
            return "dormant"
        elif user.total_transactions > 10:
            return "active"
        else:
            return "developing"

    def _get_last_processed_timestamp(self, job_id: str) -> datetime:
        """Get the last processed timestamp for an ETL job."""
        query = text("SELECT last_processed FROM etl_job_status WHERE job_id = :job_id")
        result = self.db.execute(query, {"job_id": job_id}).fetchone()
        if result:
            return result.last_processed
        return datetime.now(timezone.utc) - timedelta(hours=1)

    def _update_last_processed_timestamp(
        self, job_id: str, timestamp: datetime
    ) -> object:
        """Update the last processed timestamp for an ETL job."""
        query = text(
            "\n            INSERT INTO etl_job_status (job_id, last_processed)\n            VALUES (:job_id, :timestamp)\n            ON CONFLICT (job_id) DO UPDATE SET last_processed = :timestamp\n        "
        )
        self.db.execute(query, {"job_id": job_id, "timestamp": timestamp})
        self.db.commit()

    def get_etl_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of an ETL job."""
        if job_id not in self._etl_jobs:
            raise ValueError(f"ETL job {job_id} not found")
        job = self._etl_jobs[job_id]
        return {
            "job_id": job_id,
            "name": job.name,
            "status": job.status.value,
            "last_run": job.last_run.isoformat() if job.last_run else None,
            "next_run": job.next_run.isoformat() if job.next_run else None,
            "error_message": job.error_message,
        }

    def get_all_etl_jobs(self) -> List[Dict[str, Any]]:
        """Get status of all ETL jobs."""
        return [self.get_etl_job_status(job_id) for job_id in self._etl_jobs.keys()]

    async def refresh_all_analytics(self) -> Dict[str, Any]:
        """Refresh all analytics data by running all ETL jobs."""
        results = {}
        for job_id in self._etl_jobs.keys():
            try:
                result = await self.run_etl_job(job_id)
                results[job_id] = result
            except Exception as e:
                results[job_id] = {"status": "failed", "error": str(e)}
        return {
            "refresh_timestamp": datetime.now(timezone.utc).isoformat(),
            "job_results": results,
        }

    def create_data_mart(self, mart_name: str, query: str) -> Dict[str, Any]:
        """Create a data mart with a specific query."""
        try:
            self.db.execute(text(query))
            return {
                "mart_name": mart_name,
                "status": "created",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error creating data mart {mart_name}: {str(e)}")
            return {"mart_name": mart_name, "status": "failed", "error": str(e)}

    def get_data_lineage(self, table_name: str) -> Dict[str, Any]:
        """Get data lineage information for a table."""
        lineage = {
            "table_name": table_name,
            "source_tables": [],
            "target_tables": [],
            "etl_jobs": [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        for job_id, job in self._etl_jobs.items():
            if job.target_table == table_name:
                lineage["etl_jobs"].append(
                    {
                        "job_id": job_id,
                        "job_name": job.name,
                        "source_type": job.source_type.value,
                    }
                )
        return lineage
