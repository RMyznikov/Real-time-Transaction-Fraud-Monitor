"""Transaction domain model."""

from dataclasses import dataclass


@dataclass
class Transaction:
    """Data received for a financial transaction."""

    transaction_id: str
    account_id: str
    amount: float
    currency: str
    country: str
    timestamp: str
