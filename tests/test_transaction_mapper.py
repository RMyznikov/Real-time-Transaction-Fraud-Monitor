import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.mappers import transaction_from_json, transaction_to_json
from app.models.transaction import Transaction


def test_transaction_from_json_maps_domain_types() -> None:
    value = json.dumps(
        {
            "transaction_id": "tx-1001",
            "account_id": "acc-50",
            "amount": "125.50",
            "currency": "USD",
            "country": "US",
            "timestamp": "2026-07-18T10:00:00Z",
        }
    ).encode()

    transaction = transaction_from_json(value)

    assert transaction.transaction_id == "tx-1001"
    assert transaction.amount == Decimal("125.50")
    assert transaction.timestamp == datetime(2026, 7, 18, 10, tzinfo=timezone.utc)


def test_transaction_from_json_rejects_non_string_timestamp() -> None:
    value = json.dumps(
        {
            "transaction_id": "tx-1001",
            "account_id": "acc-50",
            "amount": "125.50",
            "currency": "USD",
            "country": "US",
            "timestamp": 123,
        }
    )

    with pytest.raises(ValueError, match="ISO 8601 string"):
        transaction_from_json(value)


def test_transaction_json_round_trip_preserves_domain_types() -> None:
    transaction = Transaction(
        transaction_id="tx-1001",
        account_id="acc-50",
        amount=Decimal("125.50"),
        currency="USD",
        country="US",
        timestamp=datetime(2026, 7, 19, 10, tzinfo=timezone.utc),
    )

    restored = transaction_from_json(transaction_to_json(transaction))

    assert restored == transaction
