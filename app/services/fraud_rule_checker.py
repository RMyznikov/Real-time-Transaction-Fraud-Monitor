from datetime import datetime, timezone

from app.consts.consts import MAX_TRANSACTION_AMOUNT
from app.models.fraud_alert import FraudAlert
from app.models.transaction import Transaction


class FraudRuleChecker:
    def check_high_amount(self, transaction: Transaction) -> FraudAlert | None:
        if transaction.amount >= MAX_TRANSACTION_AMOUNT:
            return FraudAlert(
                transaction_id=transaction.transaction_id,
                account_id=transaction.account_id,
                rule="HIGH_AMOUNT",
                risk_score=80,
                created_at=datetime.now(timezone.utc),
            )

        return None
