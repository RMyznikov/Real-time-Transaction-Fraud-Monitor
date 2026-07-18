"""Kafka consumer for transaction fraud detection."""

import json
import logging
import os
from decimal import InvalidOperation

from confluent_kafka import Consumer, KafkaError, KafkaException
from dotenv import load_dotenv

from app.enums import KafkaTopic
from app.mappers.transaction_mapper import transaction_from_json
from app.models.fraud_alert import FraudAlert
from app.services.transaction_processing_service import TransactionProcessingService

load_dotenv()

logger = logging.getLogger(__name__)


class KafkaFraudConsumer:
    """Reads transactions from Kafka and sends them through fraud processing."""

    def __init__(
        self,
        processing_service: TransactionProcessingService | None = None,
        kafka_consumer: Consumer | None = None,
    ) -> None:
        self.kafka_url = os.getenv("KAFKA_URL")
        self.topic = os.getenv("KAFKA_TOPIC", KafkaTopic.TRANSACTIONS.value)
        self.group_id = os.getenv("KAFKA_GROUP_ID", "fraud-monitor")

        if kafka_consumer is None and not self.kafka_url:
            raise ValueError("KAFKA_URL environment variable is required")

        self.processing_service = processing_service or TransactionProcessingService()
        self.consumer = kafka_consumer or Consumer(
            {
                "bootstrap.servers": self.kafka_url,
                "group.id": self.group_id,
                "auto.offset.reset": "earliest",
                # Commit only after the transaction has been handled.
                "enable.auto.commit": False,
            }
        )
        self.consumer.subscribe([self.topic])

        # All fraud alerts found during the lifetime of this consumer.
        self.fraud_alerts: list[FraudAlert] = []

    def consume(self) -> None:
        """Continuously consume Kafka messages until the process is interrupted."""
        logger.info(
            "Consuming Kafka topic %s from %s with group %s",
            self.topic,
            self.kafka_url,
            self.group_id,
        )

        try:
            while True:
                self.consume_once()
        except KeyboardInterrupt:
            logger.info("Kafka consumer interrupted")
        finally:
            self.consumer.close()

    def consume_once(self, timeout: float = 1.0) -> bool:
        """Poll and handle one message; return False when no message is available."""
        message = self.consumer.poll(timeout)
        if message is None:
            return False

        if message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                return False
            raise KafkaException(message.error())

        try:
            print(f"Event occurred with message: {message.value()}")
            fraud_alerts = self.process_message(message.value())
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            InvalidOperation,
        ) as error:
            # Invalid input cannot become valid on retry, so skip this message.
            logger.warning("Skipping invalid Kafka message: %s", error)
        else:
            self.fraud_alerts.extend(fraud_alerts)

        # Synchronous commit guarantees that the handled message is not redelivered.
        self.consumer.commit(message=message, asynchronous=False)
        return True

    def process_message(self, value: bytes | str) -> list[FraudAlert]:
        """Convert one Kafka payload and persist its transaction and alerts."""
        transaction = transaction_from_json(value)
        return self.processing_service.process_transaction(transaction)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    KafkaFraudConsumer().consume()
