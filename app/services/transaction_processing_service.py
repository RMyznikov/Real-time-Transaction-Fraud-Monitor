from app.models.transaction import Transaction
from app.repositories import transaction_repository, alert_repository
from app.services.fraud_detector import FraudDetector
from db.database import get_connection


class TransactionProcessingService:
    def __init__(self) -> None:
        self.fraud_detector = FraudDetector()

    def process_transaction(self, transaction: Transaction) -> None:
        fraud_alerts = self.fraud_detector.evaluate(transaction)

        # One connection means both repository calls belong to one transaction.
        with get_connection() as connection:
            transaction_repository.create(connection, transaction)
            alert_repository.create_many(connection, fraud_alerts)

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
