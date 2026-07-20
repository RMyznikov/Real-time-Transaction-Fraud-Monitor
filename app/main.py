from app.enums import EventType, KafkaTopic
from app.mappers.transaction_mapper import transaction_to_payload
from app.producer.transaction_producer import TransactionProducer
from app.repositories.outbox_repository import OutboxRepository
from app.services.transaction_processing_service import TransactionProcessingService
from db.database import get_connection


class FraudMonitoringApp:
    def __init__(self) -> None:
        self.t_producer = TransactionProducer()
        self.t_processor = TransactionProcessingService()


    def localFraudMonitoring(self) -> None:
        transactions = self.t_producer.produce_transactions(10, 10, 10)
        self.t_processor.process_transactions(transactions)


    def enqueue_generated_transactions(
        self,
        valid_count: int = 10_000,
        invalid_count: int = 10_000,
        fraud_count: int = 10_000,
    ) -> int:
        """Generate transactions and atomically enqueue them in the outbox."""
        transactions = self.t_producer.produce_transactions(
            valid_count,
            invalid_count,
            fraud_count,
        )

        # The main process writes events to PostgreSQL; only the worker uses Kafka.
        with get_connection() as connection:
            for transaction in transactions:
                OutboxRepository.create(
                    connection=connection,
                    topic=KafkaTopic.TRANSACTIONS,
                    event_type=EventType.TRANSACTION_CREATED,
                    event_key=transaction.account_id,
                    payload=transaction_to_payload(transaction),
                )

        return len(transactions)


    def main(self) -> None:
        self.enqueue_generated_transactions()


if __name__ == "__main__":
    fmApp = FraudMonitoringApp()
    fmApp.main()
