"""Validation and response schemas for the HTTP API."""

from datetime import datetime
from decimal import Decimal
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    country: str = Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def timestamp_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")
        return value


class TransactionCreate(TransactionInput):
    transaction_id: str = Field(min_length=1)


class TransactionResponse(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)


class FraudAlertInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    account_id: str = Field(min_length=1)
    risk_score: int = Field(ge=0, le=100)
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def created_at_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include timezone information")
        return value


class FraudAlertCreate(FraudAlertInput):
    transaction_id: str = Field(min_length=1)
    rule: str = Field(min_length=1)


class FraudAlertResponse(FraudAlertCreate):
    model_config = ConfigDict(from_attributes=True)


ItemT = TypeVar("ItemT")


class Page(BaseModel, Generic[ItemT]):
    items: list[ItemT]
    page: int
    page_size: int
    total: int
    total_pages: int


class GenerateTransactionsRequest(BaseModel):
    valid_count: int = Field(default=10_000, ge=0, le=100_000)
    invalid_count: int = Field(default=10_000, ge=0, le=100_000)
    fraud_count: int = Field(default=10_000, ge=0, le=100_000)


class GenerationAccepted(BaseModel):
    status: Literal["accepted"] = "accepted"
    transaction_count: int


class GlobalSearchItem(BaseModel):
    result_type: Literal["transaction", "fraud_alert"]
    transaction_id: str
    account_id: str
    amount: Decimal | None = None
    currency: str | None = None
    country: str | None = None
    rule: str | None = None
    risk_score: int | None = None
    occurred_at: datetime


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
