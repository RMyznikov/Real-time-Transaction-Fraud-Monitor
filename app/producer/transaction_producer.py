"""Transaction event producer."""

import random
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.consts.consts import MAX_TRANSACTION_AMOUNT
from app.models.transaction import Transaction
from app.services.transaction_validator import TransactionValidator


class TransactionProducer:
    """Creates test transactions for exercising the fraud detection flow."""

    def __init__(self) -> None:
        # This list keeps everything produced by this producer instance.
        self.transactions_list: list[Transaction] = []
        self.transaction_validator = TransactionValidator()

    def produce_valid_transaction(
        self,
        transaction: Transaction | None = None,
    ) -> Transaction:
        """Produce a valid transaction whose amount is below the fraud limit."""
        transaction = transaction or self._build_transaction(
            amount=self._random_amount(
                minimum=Decimal("0.01"),
                maximum=MAX_TRANSACTION_AMOUNT - Decimal("0.01"),
            )
        )

        # A custom transaction must really belong to the requested category.
        self.transaction_validator.validate(transaction)
        if transaction.amount >= MAX_TRANSACTION_AMOUNT:
            raise ValueError("valid transaction amount must be below fraud limit")

        return self._remember(transaction)

    def produce_invalid_transaction(
        self,
        transaction: Transaction | None = None,
    ) -> Transaction:
        """Produce a transaction rejected by validation because amount is zero."""
        transaction = transaction or self._build_transaction(amount=Decimal("0"))

        try:
            self.transaction_validator.validate(transaction)
        except (TypeError, ValueError):
            return self._remember(transaction)

        raise ValueError("invalid transaction must fail validation")

    def produce_fraud_transaction(
        self,
        transaction: Transaction | None = None,
    ) -> Transaction:
        """Produce a valid transaction detected as fraud by the amount rule."""
        transaction = transaction or self._build_transaction(
            amount=self._random_amount(
                minimum=MAX_TRANSACTION_AMOUNT,
                maximum=MAX_TRANSACTION_AMOUNT * 5,
            )
        )

        # Fraud data still has to be structurally valid before rules are checked.
        self.transaction_validator.validate(transaction)
        if transaction.amount < MAX_TRANSACTION_AMOUNT:
            raise ValueError("fraud transaction amount must reach fraud limit")

        return self._remember(transaction)

    def produce_transactions(
        self,
        valid_count: int,
        invalid_count: int,
        fraud_count: int,
    ) -> list[Transaction]:
        """Produce a batch containing the requested number of each category."""
        self._validate_counts(valid_count, invalid_count, fraud_count)

        batch = [self.produce_valid_transaction() for _ in range(valid_count)]
        batch.extend(
            self.produce_invalid_transaction() for _ in range(invalid_count)
        )
        batch.extend(self.produce_fraud_transaction() for _ in range(fraud_count))
        return batch

    def _build_transaction(self, amount: Decimal) -> Transaction:
        """Build common valid fields; callers control the amount category."""
        currency, country = random.choice(
            [("USD", "US"), ("EUR", "DE"), ("UAH", "UA"), ("CAD", "CA")]
        )

        return Transaction(
            transaction_id=f"tx-{uuid4().hex}",
            account_id=f"acc-{random.randint(1, 1000)}",
            amount=amount,
            currency=currency,
            country=country,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _random_amount(minimum: Decimal, maximum: Decimal) -> Decimal:
        """Generate an amount with exactly two decimal places."""
        minimum_cents = int(minimum * 100)
        maximum_cents = int(maximum * 100)
        return Decimal(random.randint(minimum_cents, maximum_cents)) / 100

    def _remember(self, transaction: Transaction) -> Transaction:
        """Save a produced transaction and return it to the caller."""
        self.transactions_list.append(transaction)
        return transaction

    @staticmethod
    def _validate_counts(*counts: int) -> None:
        """Reject ambiguous or impossible batch sizes early."""
        if any(isinstance(count, bool) or not isinstance(count, int) for count in counts):
            raise TypeError("transaction counts must be integers")
        if any(count < 0 for count in counts):
            raise ValueError("transaction counts must not be negative")
