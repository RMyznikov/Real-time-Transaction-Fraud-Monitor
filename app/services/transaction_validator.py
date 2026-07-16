"""Validation of incoming transaction data."""

from datetime import datetime
from decimal import Decimal

from app.models.transaction import Transaction


class TransactionValidator:
    """Checks that a transaction contains valid data."""

    def validate(self, transaction: Transaction) -> None:
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction instance")

        if not transaction.transaction_id.strip():
            raise ValueError("transaction_id must not be empty")

        if not transaction.account_id.strip():
            raise ValueError("account_id must not be empty")

        if not isinstance(transaction.amount, Decimal):
            raise ValueError("amount must be Decimal")

        if not transaction.amount.is_finite():
            raise ValueError("amount must be finite")

        if transaction.amount <= Decimal("0"):
            raise ValueError("amount must be greater than zero")

        if not self._is_valid_code(transaction.currency, 3):
            raise ValueError("currency must be a 3-letter uppercase code")

        if not self._is_valid_code(transaction.country, 2):
            raise ValueError("country must be a 2-letter uppercase code")

        self._validate_timestamp(transaction.timestamp)

    @staticmethod
    def _is_valid_code(value: str, length: int) -> bool:
        return (
            isinstance(value, str)
            and len(value) == length
            and value.isascii()
            and value.isalpha()
            and value.isupper()
        )

    @staticmethod
    def _validate_timestamp(value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("timestamp must not be empty")

        try:
            parsed_timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("timestamp must be a valid ISO 8601 value") from error

        if parsed_timestamp.tzinfo is None or parsed_timestamp.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")
