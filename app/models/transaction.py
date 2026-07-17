"""Transaction domain model."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Transaction:
    """Data received for a financial transaction."""

    transaction_id: str
    account_id: str
    amount: Decimal
    currency: str
    country: str
    timestamp: str
