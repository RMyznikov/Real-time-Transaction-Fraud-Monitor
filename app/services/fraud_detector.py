"""Fraud detection service."""

from app.models.fraud_alert import FraudAlert
from app.models.transaction import Transaction
from app.services.transaction_validator import TransactionValidator


class FraudDetector:
    def __init__(self):
        self.transaction_validator = TransactionValidator()

    def evaluate(self, transaction: Transaction) -> list[FraudAlert]:
        list_fraud_alerts = []

        # CHECKING MAX AMOUNT
        alert_high_amount = self.transaction_validator.check_high_amount(transaction)
        if alert_high_amount:
            list_fraud_alerts.append(alert_high_amount)

        return list_fraud_alerts




