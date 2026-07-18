"""Mapping helpers for fraud alert outbox payloads."""

import json
from datetime import datetime
from typing import Any

from app.models.fraud_alert import FraudAlert


def fraud_alert_from_json(value: bytes | str) -> FraudAlert:
    """Deserialize Kafka JSON into a strongly typed FraudAlert."""
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise ValueError("fraud alert JSON must contain an object")
    return fraud_alert_from_payload(payload)


def fraud_alert_from_payload(payload: dict[str, Any]) -> FraudAlert:
    """Map an outbox payload to a FraudAlert."""
    created_at = payload["created_at"]
    if not isinstance(created_at, str):
        raise ValueError("created_at must be an ISO 8601 string")

    return FraudAlert(
        transaction_id=payload["transaction_id"],
        account_id=payload["account_id"],
        rule=payload["rule"],
        risk_score=int(payload["risk_score"]),
        created_at=datetime.fromisoformat(created_at.replace("Z", "+00:00")),
    )


def fraud_alert_to_payload(alert: FraudAlert) -> dict[str, Any]:
    """Convert a FraudAlert to a JSONB-safe outbox payload."""
    return {
        "transaction_id": alert.transaction_id,
        "account_id": alert.account_id,
        "rule": alert.rule,
        "risk_score": alert.risk_score,
        "created_at": alert.created_at.isoformat(),
    }


def fraud_alert_to_json(alert: FraudAlert) -> str:
    """Serialize a FraudAlert into Kafka-ready JSON."""
    return json.dumps(fraud_alert_to_payload(alert))
