"""Types of domain events published by the application."""

from enum import Enum


class EventType(str, Enum):
    UNKNOWN = "unknown"
    TRANSACTION_CREATED = "transaction.created"
    FRAUD_ALERT_CREATED = "fraud-alert.created"
