import os

from dotenv import load_dotenv
from confluent_kafka import KafkaException, Producer

from app.enums import KafkaTopic
from app.mappers import transaction_to_json
from app.models.transaction import Transaction

load_dotenv()

class KafkaTransactionProducer:
    def __init__(self, producer: Producer | None = None) -> None:
        self.kafka_url = os.getenv('KAFKA_URL')

        if producer is None and not self.kafka_url:
            raise ValueError("KAFKA_URL environment variable is required")

        self.producer = producer or Producer({
            'bootstrap.servers': self.kafka_url,
        })
        self._delivery_errors = []

    def send(self, transaction: Transaction) -> None:
        self.producer.produce(
            topic=KafkaTopic.TRANSACTIONS.value,
            key=transaction.account_id,
            value=transaction_to_json(transaction),
            on_delivery=self._on_delivery,
        )

    def flush(self) -> None:
        remaining_messages = self.producer.flush()
        if remaining_messages:
            raise RuntimeError(
                f"{remaining_messages} transaction message(s) were not delivered"
            )

        if self._delivery_errors:
            error = self._delivery_errors.pop(0)
            self._delivery_errors.clear()
            raise KafkaException(error)

    def _on_delivery(self, error, message) -> None:
        if error is not None:
            self._delivery_errors.append(error)
