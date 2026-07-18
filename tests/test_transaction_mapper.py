import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.mappers.transaction_mapper import transaction_from_json


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
