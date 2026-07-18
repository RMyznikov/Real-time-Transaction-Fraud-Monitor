from decimal import Decimal

import pytest

from app.consts.consts import MAX_TRANSACTION_AMOUNT
from app.producer.transaction_producer import TransactionProducer
from app.services.fraud_detector import FraudDetector
from app.services.transaction_validator import TransactionValidator


def test_produce_valid_transaction() -> None:
    transaction = TransactionProducer().produce_valid_transaction()

    TransactionValidator().validate(transaction)
    assert Decimal("0") < transaction.amount < MAX_TRANSACTION_AMOUNT


def test_produce_invalid_transaction() -> None:
    transaction = TransactionProducer().produce_invalid_transaction()

    with pytest.raises(ValueError, match="amount must be greater than zero"):
        TransactionValidator().validate(transaction)


def test_produce_fraud_transaction() -> None:
    transaction = TransactionProducer().produce_fraud_transaction()

    alerts = FraudDetector().evaluate(transaction)

    assert transaction.amount >= MAX_TRANSACTION_AMOUNT
    assert len(alerts) == 1
    assert alerts[0].rule == "HIGH_AMOUNT"


def test_produce_transactions_creates_requested_batch() -> None:
    producer = TransactionProducer()

    batch = producer.produce_transactions(
        valid_count=2,
        invalid_count=3,
        fraud_count=4,
    )

    assert len(batch) == 9
    assert producer.transactions_list == batch
    assert all(item.amount < MAX_TRANSACTION_AMOUNT for item in batch[:2])
    assert all(item.amount == Decimal("0") for item in batch[2:5])
    assert all(item.amount >= MAX_TRANSACTION_AMOUNT for item in batch[5:])


@pytest.mark.parametrize("counts", [(-1, 0, 0), (0, -1, 0), (0, 0, -1)])
def test_produce_transactions_rejects_negative_counts(counts: tuple[int, int, int]) -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        TransactionProducer().produce_transactions(*counts)
