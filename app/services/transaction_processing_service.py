from app.enums import EventType, KafkaTopic
from app.mappers.fraud_alert_mapper import fraud_alert_to_payload
from app.models.fraud_alert import FraudAlert
from app.models.transaction import Transaction
from app.repositories import alert_repository, transaction_repository
from app.repositories.outbox_repository import OutboxRepository
from app.services.fraud_detector import FraudDetector
from db.database import get_connection


class TransactionProcessingService:
    def __init__(self) -> None:
        self.fraud_detector = FraudDetector()

    def process_transaction(self, transaction: Transaction) -> list[FraudAlert]:
        fraud_alerts = self.fraud_detector.evaluate(transaction)

        # One connection means both repository calls belong to one transaction.
        with get_connection() as connection:
            transaction_repository.create(connection, transaction)
            alert_repository.create_many(connection, fraud_alerts)

            # Business rows and outgoing events commit in the same transaction.
            for fraud_alert in fraud_alerts:
                OutboxRepository.create(
                    connection=connection,
                    topic=KafkaTopic.FRAUD_ALERTS,
                    event_type=EventType.FRAUD_ALERT_CREATED,
                    event_key=fraud_alert.account_id,
                    payload=fraud_alert_to_payload(fraud_alert),
                )

        # The caller can inspect alerts; Kafka publication belongs to OutboxWorker.
        return fraud_alerts

    def process_transactions(
        self,
        transactions: list[Transaction],
    ) -> list[tuple[Transaction, Exception]]:
        """Process many independent transactions and return validation failures."""
        validation_errors = []

        for transaction in transactions:
            try:
                # Each item gets its own DB transaction. One invalid item therefore
                # does not roll back the valid items processed before or after it.
                self.process_transaction(transaction)
            except (TypeError, ValueError) as error:
                validation_errors.append((transaction, error))

        return validation_errors
