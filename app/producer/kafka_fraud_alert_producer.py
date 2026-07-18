"""Kafka producer for detected fraud alerts."""

import json
import os
from dataclasses import asdict

from confluent_kafka import KafkaException, Producer
from dotenv import load_dotenv

from app.models.fraud_alert import FraudAlert

load_dotenv()


class KafkaFraudAlertProducer:
    """Publishes persisted fraud alerts for downstream consumers."""

    def __init__(self, producer: Producer | None = None) -> None:
        self.kafka_url = os.getenv("KAFKA_URL")
        self.topic = os.getenv("KAFKA_FRAUD_ALERT_TOPIC", "fraud-alerts")

        if producer is None and not self.kafka_url:
            raise ValueError("KAFKA_URL environment variable is required")

        self.producer = producer or Producer(
            {
                "bootstrap.servers": self.kafka_url,
            }
        )
        self._delivery_errors = []

    def send(self, fraud_alert: FraudAlert) -> None:
        """Queue one fraud alert for delivery to Kafka."""
        self.producer.produce(
            topic=self.topic,
            key=fraud_alert.account_id,
            value=json.dumps(
                asdict(fraud_alert),
                default=str,
            ),
            on_delivery=self._on_delivery,
        )

    def flush(self) -> None:
        """Wait for delivery and raise when Kafka could not accept an alert."""
        remaining_messages = self.producer.flush()
        if remaining_messages:
            raise RuntimeError(
                f"{remaining_messages} fraud alert message(s) were not delivered"
            )

        if self._delivery_errors:
            error = self._delivery_errors.pop(0)
            self._delivery_errors.clear()
            raise KafkaException(error)

    def _on_delivery(self, error, message) -> None:
        """Remember asynchronous delivery errors until flush is called."""
        if error is not None:
            self._delivery_errors.append(error)
