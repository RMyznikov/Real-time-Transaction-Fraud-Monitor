"""Database operations for the transactional outbox.

The caller owns the connection and decides when to commit or roll back.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.types.json import Jsonb

from app.enums import EventType, KafkaTopic
from app.models.outbox_event import OutboxEvent


class OutboxRepository:
    """Persists events that will later be delivered to Kafka."""

    @staticmethod
    def create(
        connection: psycopg.Connection,
        topic: KafkaTopic,
        event_type: EventType,
        event_key: str,
        payload: dict[str, Any],
        event_id: UUID | None = None,
    ) -> UUID:
        """Insert an unpublished event and return its UUID."""
        event_id = event_id or uuid4()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO outbox_events (
                    id,
                    topic,
                    event_type,
                    event_key,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    event_id,
                    topic.value,
                    event_type.value,
                    event_key,
                    Jsonb(payload),
                ),
            )

        return event_id

    @staticmethod
    def get_by_id(
        connection: psycopg.Connection,
        event_id: UUID,
    ) -> OutboxEvent | None:
        """Return an outbox event by UUID, or None when it does not exist."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, topic, event_type, event_key, payload,
                       created_at, published_at
                FROM outbox_events
                WHERE id = %s
                """,
                (event_id,),
            )
            row = cursor.fetchone()

        return OutboxRepository._to_event(row) if row else None

    @staticmethod
    def get_unpublished(
        connection: psycopg.Connection,
        limit: int = 100,
    ) -> list[OutboxEvent]:
        """Lock and return the oldest events that still need publishing."""
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, topic, event_type, event_key, payload,
                       created_at, published_at
                FROM outbox_events
                WHERE published_at IS NULL
                ORDER BY created_at
                LIMIT %s
                FOR UPDATE SKIP LOCKED
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        return [OutboxRepository._to_event(row) for row in rows]

    @staticmethod
    def mark_as_published(
        connection: psycopg.Connection,
        event_id: UUID,
    ) -> bool:
        """Set published_at and report whether an unpublished event was found."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE outbox_events
                SET published_at = NOW()
                WHERE id = %s AND published_at IS NULL
                """,
                (event_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete_published_before(
        connection: psycopg.Connection,
        published_before: datetime,
    ) -> int:
        """Delete old published events and return the deleted row count."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM outbox_events
                WHERE published_at IS NOT NULL
                  AND published_at < %s
                """,
                (published_before,),
            )
            return cursor.rowcount

    @staticmethod
    def _to_event(row: tuple) -> OutboxEvent:
        """Convert a PostgreSQL row into the outbox domain model."""
        return OutboxEvent(
            id=row[0],
            topic=KafkaTopic(row[1]),
            event_type=EventType(row[2]),
            event_key=row[3],
            payload=row[4],
            created_at=row[5],
            published_at=row[6],
        )
