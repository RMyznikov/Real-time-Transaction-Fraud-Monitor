"""Background worker that publishes transactional outbox events to Kafka."""

import logging
import os
from collections.abc import Callable
from threading import Event

import psycopg
from dotenv import load_dotenv

from app.enums import EventType, KafkaTopic
from app.mappers import fraud_alert_from_payload, transaction_from_payload
from app.models.outbox_event import OutboxEvent
from app.producer.kafka_fraud_alert_producer import KafkaFraudAlertProducer
from app.producer.kafka_transaction_producer import KafkaTransactionProducer
from app.repositories.outbox_repository import OutboxRepository
from db.database import get_connection

load_dotenv()

logger = logging.getLogger(__name__)


class OutboxWorker:
    """Periodically publishes unpublished outbox rows to Kafka."""

    def __init__(
        self,
        transaction_producer: KafkaTransactionProducer | None = None,
        fraud_alert_producer: KafkaFraudAlertProducer | None = None,
        connection_factory: Callable[[], psycopg.Connection] = get_connection,
        poll_interval_seconds: float | None = None,
        batch_size: int | None = None,
    ) -> None:
        self.transaction_producer = (
            transaction_producer or KafkaTransactionProducer()
        )
        self.fraud_alert_producer = (
            fraud_alert_producer or KafkaFraudAlertProducer()
        )
        self.connection_factory = connection_factory
        self.poll_interval_seconds = (
            poll_interval_seconds
            if poll_interval_seconds is not None
            else float(os.getenv("OUTBOX_POLL_INTERVAL_SECONDS", "1"))
        )
        self.batch_size = (
            batch_size
            if batch_size is not None
            else int(os.getenv("OUTBOX_BATCH_SIZE", "100"))
        )

        if self.poll_interval_seconds <= 0:
            raise ValueError("outbox poll interval must be greater than zero")
        if self.batch_size <= 0:
            raise ValueError("outbox batch size must be greater than zero")

        self._stop_event = Event()

    def run(self) -> None:
        """Run until stop() is called, retrying failed batches later."""
        logger.info(
            "Outbox worker started: interval=%ss, batch_size=%s",
            self.poll_interval_seconds,
            self.batch_size,
        )

        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                # The DB context rolls back published_at, allowing a later retry.
                logger.exception("Failed to publish outbox batch")

            self._stop_event.wait(self.poll_interval_seconds)

    def stop(self) -> None:
        """Request a graceful stop of the polling loop."""
        self._stop_event.set()

    def run_once(self) -> int:
        """Publish one locked batch and return the processed event count."""
        with self.connection_factory() as connection:
            events = OutboxRepository.get_unpublished(
                connection,
                limit=self.batch_size,
            )
            if not events:
                return 0

            used_event_types: set[EventType] = set()
            for event in events:
                self._publish(event)
                used_event_types.add(event.event_type)

            # Kafka delivery must finish before published_at is updated.
            if EventType.TRANSACTION_CREATED in used_event_types:
                self.transaction_producer.flush()
            if EventType.FRAUD_ALERT_CREATED in used_event_types:
                self.fraud_alert_producer.flush()

            for event in events:
                OutboxRepository.mark_as_published(connection, event.id)

            return len(events)

    def _publish(self, event: OutboxEvent) -> None:
        """Route an outbox event using its EventType."""
        match event.event_type:
            case EventType.TRANSACTION_CREATED:
                self._require_topic(event, KafkaTopic.TRANSACTIONS)
                self.transaction_producer.send(
                    transaction_from_payload(event.payload)
                )

            case EventType.FRAUD_ALERT_CREATED:
                self._require_topic(event, KafkaTopic.FRAUD_ALERTS)
                self.fraud_alert_producer.send(
                    fraud_alert_from_payload(event.payload)
                )

            case _:
                raise ValueError(f"Unsupported outbox event type: {event.event_type}")

    @staticmethod
    def _require_topic(event: OutboxEvent, expected: KafkaTopic) -> None:
        """Reject inconsistent EventType and KafkaTopic combinations."""
        if event.topic is not expected:
            raise ValueError(
                f"Event type {event.event_type.value} must use topic {expected.value}"
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    OutboxWorker().run()
