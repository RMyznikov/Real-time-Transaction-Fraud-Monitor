from datetime import timezone
from decimal import Decimal

from app.models.transaction import Transaction
from app.services.fraud_detector import FraudDetector


def make_transaction(amount: str) -> Transaction:
    return Transaction(
        transaction_id="tx-1001",
        account_id="acc-50",
        amount=Decimal(amount),
        currency="CAD",
        country="CA",
        timestamp="2026-07-15T20:30:00Z",
    )


def test_amount_below_limit_does_not_create_alert() -> None:
    alerts = FraudDetector().evaluate(make_transaction("9999.99"))

    assert alerts == []


def test_amount_equal_to_limit_creates_high_amount_alert() -> None:
    transaction = make_transaction("10000")

    alerts = FraudDetector().evaluate(transaction)

    assert len(alerts) == 1
    assert_high_amount_alert(alerts[0], transaction)


def test_amount_above_limit_creates_high_amount_alert() -> None:
    transaction = make_transaction("15000")

    alerts = FraudDetector().evaluate(transaction)

    assert len(alerts) == 1
    assert_high_amount_alert(alerts[0], transaction)


def assert_high_amount_alert(alert, transaction: Transaction) -> None:
    assert alert.transaction_id == transaction.transaction_id
    assert alert.account_id == transaction.account_id
    assert alert.rule == "HIGH_AMOUNT"
    assert alert.risk_score == 80
    assert alert.created_at.tzinfo == timezone.utc
