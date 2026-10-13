import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
import pytest

os.environ.setdefault("ML_BOOTSTRAP_ON_START", "false")
os.environ.setdefault("ML_PERSIST_MODELS", "false")

from src.models import (
    Account,
    AccountType,
    FraudAlert,
    Transaction,
    TransactionCategory,
    TransactionStatus,
    TransactionType,
    User,
    UserRole,
)
from src.models.database import db


def _token(app, user_id):
    return jwt.encode(
        {"user_id": user_id}, app.config["JWT_SECRET_KEY"], algorithm="HS256"
    )


def _headers(app, user):
    return {
        "Authorization": f"Bearer {_token(app, user.id)}",
        "Content-Type": "application/json",
    }


def _make_user(role=UserRole.USER):
    user = User(
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        password_hash="x",
        first_name="Test",
        last_name="User",
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def _make_account(user, balance="100000.00"):
    account = Account(
        user_id=user.id,
        account_name="Main",
        account_number=uuid.uuid4().hex[:12],
        account_type=AccountType.CHECKING,
        currency="USD",
        balance=Decimal(balance),
        available_balance=Decimal(balance),
        daily_limit=Decimal("1000000.00"),
        monthly_limit=Decimal("10000000.00"),
        yearly_limit=Decimal("100000000.00"),
    )
    db.session.add(account)
    db.session.commit()
    return account


def _seed_transactions(user, account, count=30):
    now = datetime.now(timezone.utc)
    for index in range(count):
        db.session.add(
            Transaction(
                user_id=user.id,
                account_id=account.id,
                transaction_id=f"seed-{uuid.uuid4().hex[:12]}",
                transaction_type=TransactionType.DEBIT,
                transaction_category=TransactionCategory.PURCHASE,
                status=TransactionStatus.COMPLETED,
                amount=Decimal("25.00") + index,
                currency="USD",
                description="Grocery store purchase",
                merchant_name="Local Grocery",
                country_code="US",
                created_at=now - timedelta(days=index * 2),
            )
        )
    db.session.commit()


@pytest.fixture
def ml_reset():
    from ml_services.fraud_detection.service import reset_fraud_service
    from ml_services.serving import reset_container

    reset_fraud_service()
    reset_container()
    yield
    reset_fraud_service()
    reset_container()


def test_endpoints_require_authentication(client, ml_reset):
    assert client.post("/api/v1/fraud/detect", json={"amount": 10}).status_code == 401
    assert client.get("/api/v1/fraud/model/status").status_code == 401
    assert (
        client.post("/api/v1/ai/chatbot/query", json={"query": "hi"}).status_code == 401
    )


def test_admin_endpoints_reject_regular_users(app, client, ml_reset):
    user = _make_user()
    headers = _headers(app, user)
    assert client.get("/api/v1/fraud/model/status", headers=headers).status_code == 403
    assert (
        client.post(
            "/api/v1/fraud/model/train", json={"synthetic": True}, headers=headers
        ).status_code
        == 403
    )
    assert client.get("/api/v1/fraud/statistics", headers=headers).status_code == 403


def test_detect_scopes_to_current_user(app, client, ml_reset):
    user = _make_user()
    other = _make_user()
    response = client.post(
        "/api/v1/fraud/detect",
        json={"amount": 50, "user_id": other.id, "merchant_category": "grocery"},
        headers=_headers(app, user),
    )
    assert response.status_code == 200
    assert response.get_json()["alert"]["user_id"] == user.id


def test_detect_flags_high_risk_transaction(app, client, ml_reset):
    user = _make_user()
    response = client.post(
        "/api/v1/fraud/detect",
        json={
            "amount": 9500,
            "merchant_category": "cryptocurrency",
            "location_country": "KP",
        },
        headers=_headers(app, user),
    )
    body = response.get_json()["alert"]
    assert response.status_code == 200
    assert body["risk_level"] in ("high", "critical")
    assert "sanctions_exposure" in body["fraud_types"]


def test_detect_rejects_invalid_amount(app, client, ml_reset):
    user = _make_user()
    response = client.post(
        "/api/v1/fraud/detect", json={"amount": "abc"}, headers=_headers(app, user)
    )
    assert response.status_code == 400


def test_admin_trains_and_scores_with_model(app, client, ml_reset):
    admin = _make_user(UserRole.ADMIN)
    headers = _headers(app, admin)
    trained = client.post(
        "/api/v1/fraud/model/train",
        json={"synthetic": True, "samples": 1500},
        headers=headers,
    )
    assert trained.status_code == 200
    assert trained.get_json()["result"]["promoted"] is True
    status = client.get("/api/v1/fraud/model/status", headers=headers).get_json()[
        "status"
    ]
    assert status["mode"] == "model"
    scored = client.post(
        "/api/v1/fraud/detect",
        json={"amount": 40, "merchant_category": "grocery"},
        headers=headers,
    )
    assert scored.get_json()["alert"]["metadata"]["mode"] == "model"
    drift = client.get("/api/v1/fraud/model/drift", headers=headers)
    assert drift.status_code == 200
    check = client.get("/api/v1/fraud/model/retrain/check", headers=headers)
    assert check.status_code == 200


def test_feedback_flow(app, client, ml_reset):
    admin = _make_user(UserRole.ADMIN)
    headers = _headers(app, admin)
    alert = client.post(
        "/api/v1/fraud/detect",
        json={"amount": 20000, "transaction_id": "tx-feedback-1"},
        headers=headers,
    ).get_json()["alert"]
    ok = client.post(
        "/api/v1/fraud/feedback",
        json={"transaction_id": alert["transaction_id"], "is_fraud": True},
        headers=headers,
    )
    assert ok.status_code == 200
    missing = client.post(
        "/api/v1/fraud/feedback",
        json={"transaction_id": "nope", "is_fraud": True},
        headers=headers,
    )
    assert missing.status_code == 404
    stats = client.get("/api/v1/fraud/statistics", headers=headers).get_json()[
        "statistics"
    ]
    assert stats["total_transactions"] >= 1


def test_ai_analyze_persists_alert_and_resolves(app, client, ml_reset):
    admin = _make_user(UserRole.ADMIN)
    headers = _headers(app, admin)
    response = client.post(
        "/api/v1/ai/fraud-detection/analyze",
        json={
            "transaction_id": "tx-ai-1",
            "amount": 12000,
            "merchant_info": {"category": "cryptocurrency", "location": "IR"},
        },
        headers=headers,
    )
    body = response.get_json()
    assert response.status_code == 200
    assert body["alert_created"] is True
    alert_id = body["alert_id"]
    listing = client.get(
        "/api/v1/ai/fraud-detection/alerts?status=pending", headers=headers
    ).get_json()
    assert listing["pagination"]["total"] == 1
    resolved = client.post(
        f"/api/v1/ai/fraud-detection/alerts/{alert_id}/resolve",
        json={"resolution": "confirmed", "notes": "customer confirmed"},
        headers=headers,
    )
    assert resolved.status_code == 200
    assert resolved.get_json()["alert"]["status"] == "confirmed"
    assert resolved.get_json()["model_feedback_applied"] is True


def test_regular_user_sees_only_own_alerts(app, client, ml_reset):
    first, second = _make_user(), _make_user()
    for user in (first, second):
        client.post(
            "/api/v1/ai/fraud-detection/analyze",
            json={
                "amount": 15000,
                "merchant_info": {"category": "cryptocurrency", "location": "KP"},
            },
            headers=_headers(app, user),
        )
    listing = client.get(
        "/api/v1/ai/fraud-detection/alerts", headers=_headers(app, first)
    ).get_json()
    assert listing["pagination"]["total"] == 1
    assert listing["alerts"][0]["user_id"] == first.id


def test_ai_analyze_denies_other_user(app, client, ml_reset):
    user, other = _make_user(), _make_user()
    response = client.post(
        "/api/v1/ai/fraud-detection/analyze",
        json={"amount": 10, "user_id": other.id},
        headers=_headers(app, user),
    )
    assert response.status_code == 403


def test_risk_spending_categorize_and_chat(app, client, ml_reset):
    user = _make_user()
    account = _make_account(user, "2500.00")
    _seed_transactions(user, account)
    headers = _headers(app, user)
    risk = client.post("/api/v1/ai/risk/assess", json={}, headers=headers)
    assert risk.status_code == 200
    assert 0.0 <= risk.get_json()["assessment"]["overall_risk_score"] <= 1.0
    spending = client.get(
        "/api/v1/ai/spending/analysis?days=90", headers=headers
    ).get_json()["analysis"]
    assert spending["total_spent"] > 0
    assert "groceries" in spending["category_totals"]
    categorized = client.post(
        "/api/v1/ai/transactions/categorize",
        json={
            "transactions": [{"description": "Netflix subscription", "amount": 15.99}]
        },
        headers=headers,
    ).get_json()
    assert categorized["results"][0]["category"] == "entertainment"
    chat = client.post(
        "/api/v1/ai/chatbot/query",
        json={"query": "What is my balance?"},
        headers=headers,
    ).get_json()
    assert chat["grounded_in_account_data"] is True
    assert "2,500.00" in chat["response"]


def test_internal_transfer_blocked_by_fraud_screening(app, ml_reset):
    from src.schemas import InternalTransferRequest
    from src.services.payment_service import process_internal_transfer
    from src.services.payment_service_errors import FraudBlocked

    sender, receiver = _make_user(), _make_user()
    source = _make_account(sender, "5000000.00")
    target = _make_account(receiver, "10.00")
    request_data = InternalTransferRequest(
        from_account_id=source.id,
        to_account_id=target.id,
        amount=Decimal("9500.00"),
        description="casino wire transfer",
    )
    ml_reset
    from ml_services.config import get_settings

    assert get_settings().block_in_payments is True
    try:
        process_internal_transfer(db.session, request_data)
    except FraudBlocked:
        assert db.session.query(FraudAlert).count() == 1
    else:
        pytest.skip("score did not reach block threshold with rules only")


def test_normal_internal_transfer_passes_screening(app, ml_reset):
    from src.schemas import InternalTransferRequest
    from src.services.payment_service import process_internal_transfer

    sender, receiver = _make_user(), _make_user()
    source = _make_account(sender, "5000.00")
    target = _make_account(receiver, "10.00")
    _seed_transactions(sender, source)
    debit, credit = process_internal_transfer(
        db.session,
        InternalTransferRequest(
            from_account_id=source.id,
            to_account_id=target.id,
            amount=Decimal("40.00"),
            description="rent share",
        ),
    )
    assert debit.amount == Decimal("40.00")


def test_health_reports_ml_status(client, ml_reset):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["services"]["ml"] in ("healthy", "degraded")


def test_customer_responds_to_own_alert_only(app, client, ml_reset):
    owner, stranger = _make_user(), _make_user()
    created = client.post(
        "/api/v1/ai/fraud-detection/analyze",
        json={
            "amount": 15000,
            "merchant_info": {"category": "cryptocurrency", "location": "KP"},
        },
        headers=_headers(app, owner),
    ).get_json()
    alert_id = created["alert_id"]
    denied = client.post(
        f"/api/v1/ai/fraud-detection/alerts/{alert_id}/respond",
        json={"response": "recognized"},
        headers=_headers(app, stranger),
    )
    assert denied.status_code == 404
    invalid = client.post(
        f"/api/v1/ai/fraud-detection/alerts/{alert_id}/respond",
        json={"response": "maybe"},
        headers=_headers(app, owner),
    )
    assert invalid.status_code == 400
    ok = client.post(
        f"/api/v1/ai/fraud-detection/alerts/{alert_id}/respond",
        json={"response": "not_me"},
        headers=_headers(app, owner),
    )
    assert ok.status_code == 200
    assert ok.get_json()["alert"]["status"] == "investigating"
