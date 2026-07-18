import json
import os
from dataclasses import asdict

from dotenv import load_dotenv
from confluent_kafka import Producer

from app.models.transaction import Transaction

load_dotenv()

class KafkaTransactionProducer:
    def __init__(self) -> None:
        self.kafka_url = os.getenv('KAFKA_URL')

        self.producer = Producer({
            'bootstrap.servers': self.kafka_url,
        })

    def send(self, transaction: Transaction) -> None:
        self.producer.produce(
            topic="transactions",
            key=transaction.account_id,
            value=json.dumps(
                asdict(transaction),
                default=str,
            ),
        )

    def flush(self) -> None:
        self.producer.flush()