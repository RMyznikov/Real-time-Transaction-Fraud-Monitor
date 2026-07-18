"""Kafka topic names used by the application."""

from enum import Enum


class KafkaTopic(str, Enum):
    TRANSACTIONS = "transactions"
    FRAUD_ALERTS = "fraud-alerts"
