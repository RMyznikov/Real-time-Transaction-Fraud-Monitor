from datetime import datetime

from app.consts.consts import MAX_TRANSACTION_AMOUNT
from app.models.fraud_alert import FraudAlert
from app.models.transaction import Transaction


class TransactionValidator:
    def check_high_amount(self, transaction: Transaction) -> FraudAlert | None:
        if transaction.amount > MAX_TRANSACTION_AMOUNT:
            return FraudAlert(transaction.transaction_id, transaction.account_id, 'Transaction amount is too high', 80, datetime.now())
        else:
            return None
