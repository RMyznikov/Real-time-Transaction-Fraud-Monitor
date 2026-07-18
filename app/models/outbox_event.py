"""Transactional outbox event model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.enums import EventType, KafkaTopic


@dataclass
class OutboxEvent:
    """Event waiting to be published from PostgreSQL to Kafka."""

    id: UUID
    topic: KafkaTopic
    event_type: EventType
    event_key: str
    payload: dict[str, Any]
    created_at: datetime
    published_at: datetime | None
