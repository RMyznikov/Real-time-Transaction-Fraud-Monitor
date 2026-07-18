from app.enums import EventType, KafkaTopic
from app.mappers.transaction_mapper import transaction_to_payload
from app.producer.transaction_producer import TransactionProducer
from app.repositories.outbox_repository import OutboxRepository
from app.services.transaction_processing_service import TransactionProcessingService
from app.workers.outbox_worker import OutboxWorker
from db.database import get_connection


class FraudMonitoringApp:
    def __init__(self) -> None:
        self.t_producer = TransactionProducer()
        self.t_processor = TransactionProcessingService()


    def localFraudMonitoring(self) -> None:
        transactions = self.t_producer.produce_transactions(10, 10, 10)
        self.t_processor.process_transactions(transactions)


    def main(self) -> None:
        transactions = self.t_producer.produce_transactions(1200, 100, 100)

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


if __name__ == "__main__":
    fmApp = FraudMonitoringApp()
    fmApp.main()
