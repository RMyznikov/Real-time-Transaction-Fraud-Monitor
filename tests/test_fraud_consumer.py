import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

from confluent_kafka import KafkaError

from app.consumer.kafka_fraud_consumer import KafkaFraudConsumer
from app.models.fraud_alert import FraudAlert


def make_message_value(amount: str = "15000.00") -> bytes:
    return json.dumps(
        {
            "transaction_id": "tx-1001",
            "account_id": "acc-50",
            "amount": amount,
            "currency": "USD",
            "country": "US",
            "timestamp": "2026-07-18T10:00:00+00:00",
        }
    ).encode()


def test_process_message_deserializes_and_returns_fraud_alerts() -> None:
    alert = FraudAlert(
        transaction_id="tx-1001",
        account_id="acc-50",
        rule="HIGH_AMOUNT",
        risk_score=80,
        created_at=datetime.now(timezone.utc),
    )
    processing_service = Mock()
    processing_service.process_transaction.return_value = [alert]
    kafka_consumer = Mock()
    consumer = KafkaFraudConsumer(processing_service, kafka_consumer)

    alerts = consumer.process_message(make_message_value())

    transaction = processing_service.process_transaction.call_args.args[0]
    assert transaction.amount == Decimal("15000.00")
    assert transaction.timestamp == datetime(2026, 7, 18, 10, tzinfo=timezone.utc)
    assert alerts == [alert]


def test_consume_once_stores_alert_and_commits_message() -> None:
    alert = Mock(spec=FraudAlert)
    processing_service = Mock()
    processing_service.process_transaction.return_value = [alert]
    message = Mock()
    message.error.return_value = None
    message.value.return_value = make_message_value()
    kafka_consumer = Mock()
    kafka_consumer.poll.return_value = message
    consumer = KafkaFraudConsumer(processing_service, kafka_consumer)

    consumed = consumer.consume_once()

    assert consumed is True
    assert consumer.fraud_alerts == [alert]
    kafka_consumer.commit.assert_called_once_with(
        message=message,
        asynchronous=False,
    )


def test_consume_once_skips_invalid_message_and_commits_offset() -> None:
    processing_service = Mock()
    message = Mock()
    message.error.return_value = None
    message.value.return_value = b"not-json"
    kafka_consumer = Mock()
    kafka_consumer.poll.return_value = message
    consumer = KafkaFraudConsumer(processing_service, kafka_consumer)

    consumed = consumer.consume_once()

    assert consumed is True
    processing_service.process_transaction.assert_not_called()
    kafka_consumer.commit.assert_called_once()


def test_consume_once_waits_when_topic_metadata_is_not_ready() -> None:
    processing_service = Mock()
    error = Mock()
    error.code.return_value = KafkaError.UNKNOWN_TOPIC_OR_PART
    message = Mock()
    message.error.return_value = error
    kafka_consumer = Mock()
    kafka_consumer.poll.return_value = message
    consumer = KafkaFraudConsumer(processing_service, kafka_consumer)

    consumed = consumer.consume_once()

    assert consumed is False
    processing_service.process_transaction.assert_not_called()
    kafka_consumer.commit.assert_not_called()
