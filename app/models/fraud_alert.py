"""Fraud alert domain model."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FraudAlert:
    """Data received for a financial transaction."""

    transaction_id: str
    account_id: str
    rule: str
    risk_score: int
    created_at: datetime
