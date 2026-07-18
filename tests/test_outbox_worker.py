from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, call, patch
from uuid import uuid4

import pytest

from app.enums import EventType, KafkaTopic
from app.models.outbox_event import OutboxEvent
from app.repositories.outbox_repository import OutboxRepository
from app.workers.outbox_worker import OutboxWorker


def make_event(
    event_type: EventType,
    topic: KafkaTopic,
    payload: dict,
) -> OutboxEvent:
    return OutboxEvent(
        id=uuid4(),
        topic=topic,
        event_type=event_type,
        event_key="acc-50",
        payload=payload,
        created_at=datetime.now(timezone.utc),
        published_at=None,
    )


def test_run_once_routes_events_flushes_and_marks_them_published() -> None:
    transaction_event = make_event(
        EventType.TRANSACTION_CREATED,
        KafkaTopic.TRANSACTIONS,
        {
            "transaction_id": "tx-1001",
            "account_id": "acc-50",
            "amount": "125.50",
            "currency": "USD",
            "country": "US",
            "timestamp": "2026-07-18T10:00:00+00:00",
        },
    )
    alert_event = make_event(
        EventType.FRAUD_ALERT_CREATED,
        KafkaTopic.FRAUD_ALERTS,
        {
            "transaction_id": "tx-1001",
            "account_id": "acc-50",
            "rule": "HIGH_AMOUNT",
            "risk_score": 80,
            "created_at": "2026-07-18T10:00:01+00:00",
        },
    )
    connection = MagicMock()
    connection.__enter__.return_value = connection
    transaction_producer = Mock()
    alert_producer = Mock()
    worker = OutboxWorker(
        transaction_producer=transaction_producer,
        fraud_alert_producer=alert_producer,
        connection_factory=Mock(return_value=connection),
        poll_interval_seconds=1,
        batch_size=10,
    )

    with (
        patch.object(
            OutboxRepository,
            "get_unpublished",
            return_value=[transaction_event, alert_event],
        ),
        patch.object(OutboxRepository, "mark_as_published") as mark_published,
    ):
        processed = worker.run_once()

    assert processed == 2
    assert transaction_producer.send.call_args.args[0].transaction_id == "tx-1001"
    assert alert_producer.send.call_args.args[0].rule == "HIGH_AMOUNT"
    transaction_producer.flush.assert_called_once_with()
    alert_producer.flush.assert_called_once_with()
    assert mark_published.call_args_list == [
        call(connection, transaction_event.id),
        call(connection, alert_event.id),
    ]


def test_worker_rejects_event_type_topic_mismatch() -> None:
    event = make_event(
        EventType.FRAUD_ALERT_CREATED,
        KafkaTopic.TRANSACTIONS,
        {},
    )
    worker = OutboxWorker(
        transaction_producer=Mock(),
        fraud_alert_producer=Mock(),
        connection_factory=Mock(),
        poll_interval_seconds=1,
        batch_size=10,
    )

    with pytest.raises(ValueError, match="must use topic fraud-alerts"):
        worker._publish(event)
