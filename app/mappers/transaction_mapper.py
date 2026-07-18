"""Convert external transaction payloads into domain models."""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.models.transaction import Transaction


def transaction_from_json(value: bytes | str) -> Transaction:
    """Deserialize producer JSON into a strongly typed Transaction."""
    payload: dict[str, Any] = json.loads(value)
    timestamp = payload["timestamp"]
    if not isinstance(timestamp, str):
        raise ValueError("timestamp must be an ISO 8601 string")

    return Transaction(
        transaction_id=payload["transaction_id"],
        account_id=payload["account_id"],
        amount=Decimal(str(payload["amount"])),
        currency=payload["currency"],
        country=payload["country"],
        timestamp=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
    )
