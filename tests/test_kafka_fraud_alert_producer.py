import json
from datetime import datetime, timezone
from unittest.mock import Mock

from app.models.fraud_alert import FraudAlert
from app.producer.kafka_fraud_alert_producer import KafkaFraudAlertProducer


def test_send_produces_serialized_fraud_alert() -> None:
    kafka_producer = Mock()
    producer = KafkaFraudAlertProducer(kafka_producer)
    alert = FraudAlert(
        transaction_id="tx-1001",
        account_id="acc-50",
        rule="HIGH_AMOUNT",
        risk_score=80,
        created_at=datetime(2026, 7, 18, 10, tzinfo=timezone.utc),
    )

    producer.send(alert)

    call = kafka_producer.produce.call_args
    assert call.kwargs["topic"] == "fraud-alerts"
    assert call.kwargs["key"] == "acc-50"
    assert json.loads(call.kwargs["value"])["rule"] == "HIGH_AMOUNT"
    assert callable(call.kwargs["on_delivery"])
