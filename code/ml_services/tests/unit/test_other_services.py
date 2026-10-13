from datetime import datetime, timedelta, timezone

import numpy as np
from ml_services.evaluation import (
    classification_metrics,
    group_fairness_report,
    walk_forward_validation,
)
from ml_services.fraud_detection import RandomForestFraudModel
from ml_services.monitoring import (
    PerformanceTracker,
    compute_drift,
    population_stability_index,
)
from ml_services.risk_assessment import AIRiskAssessor, RiskTier
from ml_services.support_chatbot import FlowletAIChatbot, QueryType, redact_pii
from ml_services.transaction_intelligence import (
    AITransactionCategorizer,
    SpendingAnalyzer,
    TransactionCategory,
    detect_recurring,
)


def _tx_history(count=40):
    now = datetime.now(timezone.utc)
    return [
        {
            "timestamp": (now - timedelta(days=index * 3)).isoformat(),
            "amount": 50 + index,
            "type": "credit" if index % 5 == 0 else "debit",
            "status": "completed",
            "location_country": "US",
            "device_fingerprint": "d1",
        }
        for index in range(count)
    ]


def test_risk_assessment_with_and_without_data():
    assessor = AIRiskAssessor()
    rich = assessor.assess_user_risk(
        "u1",
        user_data={
            "transaction_history": _tx_history(),
            "account_balances": {"available": 5000},
            "kyc_status": "verified",
            "account_age_days": 500,
            "payment_history": [{"status": "on_time"}] * 8,
        },
    )
    sparse = assessor.assess_user_risk("u2")
    assert rich.overall_risk_level in (RiskTier.VERY_LOW, RiskTier.LOW)
    assert rich.confidence_score > sparse.confidence_score
    assert set(rich.category_scores) == {
        "credit_risk",
        "fraud_risk",
        "liquidity_risk",
        "operational_risk",
        "compliance_risk",
    }


def test_risk_rises_with_bad_signals():
    assessor = AIRiskAssessor()
    risky = assessor.assess_user_risk(
        "u3",
        user_data={
            "kyc_status": "rejected",
            "fraud_alert_scores": [0.9, 0.95],
            "security_incidents": ["a", "b", "c"],
            "payment_history": [{"status": "late"}] * 5,
            "compliance_records": [{"status": "violation"}] * 2,
        },
    )
    safe = assessor.assess_user_risk(
        "u4", user_data={"kyc_status": "verified", "account_age_days": 900}
    )
    assert risky.overall_risk_score > safe.overall_risk_score + 0.2
    assert risky.recommendations and risky.monitoring_alerts


def test_risk_report_trend():
    assessor = AIRiskAssessor()
    for _ in range(4):
        report = assessor.generate_risk_report("trend-user", {"kyc_status": "verified"})
    assert report["trend"] in {"stable", "improving", "worsening"}


def test_categorizer_rules_mcc_and_corrections():
    categorizer = AITransactionCategorizer()
    assert (
        categorizer.categorize_transaction({"description": "Starbucks Coffee"}).category
        == TransactionCategory.RESTAURANTS
    )
    assert (
        categorizer.categorize_transaction(
            {"description": "x", "merchant_category_code": "5411"}
        ).category
        == TransactionCategory.GROCERIES
    )
    unknown = {"description": "Zyxq Holdings 8841", "amount": 12}
    assert (
        categorizer.categorize_transaction(unknown, "u").category
        == TransactionCategory.OTHER
    )
    assert categorizer.update_user_profile("u", unknown, "education") is True
    assert (
        categorizer.categorize_transaction(unknown, "u").category
        == TransactionCategory.EDUCATION
    )
    assert categorizer.update_user_profile("u", unknown, "not_a_category") is False


def test_recurring_detection_and_spending_analysis():
    now = datetime.now(timezone.utc)
    transactions = [
        {
            "description": "Netflix",
            "amount": 15.99,
            "timestamp": (now - timedelta(days=30 * k + 1)).isoformat(),
            "type": "debit",
        }
        for k in range(4)
    ]
    transactions += [
        {
            "description": "Grocery store",
            "amount": 30 + k % 5,
            "timestamp": (now - timedelta(days=k)).isoformat(),
            "type": "debit",
        }
        for k in range(80)
    ]
    transactions.append(
        {
            "description": "Salary payroll",
            "amount": 3000,
            "timestamp": (now - timedelta(days=5)).isoformat(),
            "type": "credit",
        }
    )
    recurring = detect_recurring(transactions)
    assert any(
        item["merchant"] == "netflix" and item["period_days"] == 30
        for item in recurring
    )
    analysis = (
        SpendingAnalyzer().analyze_spending_patterns("u", transactions, 90).to_dict()
    )
    assert analysis["total_income"] == 3000
    assert next(iter(analysis["category_totals"])) == "groceries"
    assert analysis["forecast"]["projected_spend"] is not None


def test_chatbot_grounds_answers_and_escalates():
    bot = FlowletAIChatbot()
    context = {
        "balances": {"USD": 1250.5},
        "recent_transactions": [
            {"description": "Coffee", "amount": 4.5, "type": "debit"}
        ],
    }
    balance = bot.respond("u", "What is my balance?", "s", context)
    assert balance.grounded_in_account_data and "1,250.50" in balance.response_text
    assert balance.query_type == QueryType.ACCOUNT_BALANCE
    ungrounded = bot.respond("u", "What is my balance?", "s2", {})
    assert not ungrounded.grounded_in_account_data and ungrounded.confidence <= 0.6
    fraud = bot.respond("u", "someone made an unauthorized charge on my card", "s3")
    assert fraud.escalate_to_human is True
    assert bot.respond("u", "hello", "s4").query_type == QueryType.GREETING
    assert bot.respond("u", "   ", "s5").confidence < 0.5


def test_chatbot_redacts_pii():
    text, count = redact_pii("card 4111 1111 1111 1111 email a@b.com")
    assert "4111" not in text and "a@b.com" not in text and count == 2


def test_evaluation_metrics_and_fairness():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 600)
    scores = np.clip(y * 0.6 + rng.normal(0.2, 0.2, 600), 0, 1)
    metrics = classification_metrics(y, scores, 0.5)
    assert metrics["roc_auc"] > 0.9 and "recall_at_1pct_fpr" in metrics
    groups = np.where(rng.random(600) > 0.5, "a", "b")
    report = group_fairness_report(y, scores, groups)
    assert set(report["groups"]) == {"a", "b"} and "disparity" in report


def test_walk_forward_validation(labeled_data):
    features, labels = labeled_data
    result = walk_forward_validation(
        features,
        labels,
        lambda: RandomForestFraudModel({"n_estimators": 30}),
        n_splits=3,
    )
    assert result["folds"] and result["mean_roc_auc"] > 0.85


def test_drift_metrics():
    rng = np.random.default_rng(1)
    import pandas as pd

    base = pd.DataFrame({"a": rng.normal(0, 1, 1000), "b": rng.normal(5, 1, 1000)})
    same = pd.DataFrame({"a": rng.normal(0, 1, 500), "b": rng.normal(5, 1, 500)})
    shifted = pd.DataFrame({"a": rng.normal(2, 1, 500), "b": rng.normal(5, 1, 500)})
    assert population_stability_index(base["a"], same["a"]) < 0.1
    assert not compute_drift(base, same).drifted
    report = compute_drift(base, shifted)
    assert report.drifted and report.drifted_features == ["a"]


def test_performance_tracker():
    tracker = PerformanceTracker()
    for latency in (5, 10, 15):
        tracker.record(latency, 0.1, "allow", "model")
    tracker.record_error()
    snapshot = tracker.snapshot()
    assert snapshot["requests"] == 3 and snapshot["errors"] == 1
    assert snapshot["latency_ms"]["p50"] == 10
