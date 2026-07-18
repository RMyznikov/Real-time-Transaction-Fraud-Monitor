"""Convert external transaction payloads into domain models."""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.models.transaction import Transaction


def transaction_from_json(value: bytes | str) -> Transaction:
    """Deserialize producer JSON into a strongly typed Transaction."""
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise ValueError("transaction JSON must contain an object")
    return transaction_from_payload(payload)


def transaction_from_payload(payload: dict[str, Any]) -> Transaction:
    """Map an outbox or JSON payload to a Transaction."""
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


def transaction_to_payload(transaction: Transaction) -> dict[str, Any]:
    """Convert a Transaction to a JSONB-safe outbox payload."""
    return {
        "transaction_id": transaction.transaction_id,
        "account_id": transaction.account_id,
        "amount": str(transaction.amount),
        "currency": transaction.currency,
        "country": transaction.country,
        "timestamp": transaction.timestamp.isoformat(),
    }


def transaction_to_json(transaction: Transaction) -> str:
    """Serialize a Transaction into Kafka-ready JSON."""
    return json.dumps(transaction_to_payload(transaction))
