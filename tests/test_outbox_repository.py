from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from psycopg.types.json import Jsonb

from app.enums import EventType, KafkaTopic
from app.repositories.outbox_repository import OutboxRepository


def make_connection() -> tuple[MagicMock, MagicMock]:
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    return connection, cursor


def test_create_inserts_typed_outbox_event() -> None:
    connection, cursor = make_connection()
    event_id = uuid4()
    payload = {"transaction_id": "tx-1001", "amount": "15000.00"}

    result = OutboxRepository.create(
        connection=connection,
        topic=KafkaTopic.FRAUD_ALERTS,
        event_type=EventType.FRAUD_ALERT_CREATED,
        event_key="acc-50",
        payload=payload,
        event_id=event_id,
    )

    parameters = cursor.execute.call_args.args[1]
    assert result == event_id
    assert parameters[:4] == (
        event_id,
        "fraud-alerts",
        "fraud-alert.created",
        "acc-50",
    )
    assert isinstance(parameters[4], Jsonb)
    assert parameters[4].obj == payload


def test_get_unpublished_maps_rows_to_events_and_locks_them() -> None:
    connection, cursor = make_connection()
    event_id = uuid4()
    created_at = datetime.now(timezone.utc)
    cursor.fetchall.return_value = [
        (
            event_id,
            "fraud-alerts",
            "fraud-alert.created",
            "acc-50",
            {"transaction_id": "tx-1001"},
            created_at,
            None,
        )
    ]

    events = OutboxRepository.get_unpublished(connection, limit=25)

    sql = cursor.execute.call_args.args[0]
    assert "FOR UPDATE SKIP LOCKED" in sql
    assert cursor.execute.call_args.args[1] == (25,)
    assert events[0].id == event_id
    assert events[0].topic is KafkaTopic.FRAUD_ALERTS
    assert events[0].event_type is EventType.FRAUD_ALERT_CREATED
    assert events[0].published_at is None


def test_mark_as_published_reports_updated_event() -> None:
    connection, cursor = make_connection()
    cursor.rowcount = 1

    updated = OutboxRepository.mark_as_published(connection, uuid4())

    assert updated is True


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_get_unpublished_rejects_invalid_limit(limit) -> None:
    connection, _ = make_connection()

    with pytest.raises(ValueError, match="positive integer"):
        OutboxRepository.get_unpublished(connection, limit=limit)
