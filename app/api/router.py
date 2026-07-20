"""REST endpoints for transactions, fraud alerts and monitoring search."""

from math import ceil
from typing import Annotated

import psycopg
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Response, status

from app.api.schemas import (
    FraudAlertCreate,
    FraudAlertInput,
    FraudAlertResponse,
    GenerateTransactionsRequest,
    GenerationAccepted,
    GlobalSearchItem,
    Page,
    TransactionCreate,
    TransactionInput,
    TransactionResponse,
)
from app.main import FraudMonitoringApp
from app.models.fraud_alert import FraudAlert
from app.models.transaction import Transaction
from app.repositories import alert_repository, search_repository, transaction_repository
from db.database import get_connection

router = APIRouter(prefix="/api")
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]
SearchText = Annotated[str | None, Query(max_length=200)]


def _page(items: list, page: int, page_size: int, total: int) -> dict:
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size),
    }


def _transaction(model: TransactionCreate | TransactionInput, transaction_id: str) -> Transaction:
    return Transaction(
        transaction_id=transaction_id,
        account_id=model.account_id,
        amount=model.amount,
        currency=model.currency,
        country=model.country,
        timestamp=model.timestamp,
    )


def _alert(
    model: FraudAlertCreate | FraudAlertInput,
    transaction_id: str,
    rule: str,
) -> FraudAlert:
    return FraudAlert(
        transaction_id=transaction_id,
        account_id=model.account_id,
        rule=rule,
        risk_score=model.risk_score,
        created_at=model.created_at,
    )


def _raise_integrity_error(error: psycopg.IntegrityError) -> None:
    if isinstance(error, psycopg.errors.UniqueViolation):
        raise HTTPException(status_code=409, detail="Resource already exists") from error
    if isinstance(error, psycopg.errors.ForeignKeyViolation):
        raise HTTPException(
            status_code=409,
            detail="Referenced transaction does not exist",
        ) from error
    raise HTTPException(status_code=422, detail="Database constraint violation") from error


@router.get("/transactions", response_model=Page[TransactionResponse])
def list_transactions(
    page: PageNumber = 1,
    page_size: PageSize = 40,
    search: SearchText = None,
) -> dict:
    with get_connection() as connection:
        items, total = transaction_repository.get_page(connection, page, page_size, search)
    return _page(items, page, page_size, total)


@router.post(
    "/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(payload: TransactionCreate) -> Transaction:
    transaction = _transaction(payload, payload.transaction_id)
    try:
        with get_connection() as connection:
            transaction_repository.create(connection, transaction)
    except psycopg.IntegrityError as error:
        _raise_integrity_error(error)
    return transaction


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str) -> Transaction:
    with get_connection() as connection:
        transaction = transaction_repository.get_by_id(connection, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: str, payload: TransactionInput) -> Transaction:
    transaction = _transaction(payload, transaction_id)
    try:
        with get_connection() as connection:
            updated = transaction_repository.update(connection, transaction)
    except psycopg.IntegrityError as error:
        _raise_integrity_error(error)
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: str) -> Response:
    with get_connection() as connection:
        deleted = transaction_repository.delete(connection, transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/fraud-alerts", response_model=Page[FraudAlertResponse])
def list_fraud_alerts(
    page: PageNumber = 1,
    page_size: PageSize = 40,
    search: SearchText = None,
) -> dict:
    with get_connection() as connection:
        items, total = alert_repository.get_page(connection, page, page_size, search)
    return _page(items, page, page_size, total)


@router.post(
    "/fraud-alerts",
    response_model=FraudAlertResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fraud_alert(payload: FraudAlertCreate) -> FraudAlert:
    alert = _alert(payload, payload.transaction_id, payload.rule)
    try:
        with get_connection() as connection:
            alert_repository.create(connection, alert)
    except psycopg.IntegrityError as error:
        _raise_integrity_error(error)
    return alert


@router.get(
    "/fraud-alerts/{transaction_id}/{rule}",
    response_model=FraudAlertResponse,
)
def get_fraud_alert(transaction_id: str, rule: str) -> FraudAlert:
    with get_connection() as connection:
        alert = alert_repository.get(connection, transaction_id, rule)
    if alert is None:
        raise HTTPException(status_code=404, detail="Fraud alert not found")
    return alert


@router.put(
    "/fraud-alerts/{transaction_id}/{rule}",
    response_model=FraudAlertResponse,
)
def update_fraud_alert(
    transaction_id: str,
    rule: str,
    payload: FraudAlertInput,
) -> FraudAlert:
    alert = _alert(payload, transaction_id, rule)
    try:
        with get_connection() as connection:
            updated = alert_repository.update(connection, alert)
    except psycopg.IntegrityError as error:
        _raise_integrity_error(error)
    if not updated:
        raise HTTPException(status_code=404, detail="Fraud alert not found")
    return alert


@router.delete(
    "/fraud-alerts/{transaction_id}/{rule}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_fraud_alert(transaction_id: str, rule: str) -> Response:
    with get_connection() as connection:
        deleted = alert_repository.delete(connection, transaction_id, rule)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fraud alert not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/search", response_model=Page[GlobalSearchItem])
def global_search(
    query: Annotated[str, Query(min_length=1, max_length=200)],
    page: PageNumber = 1,
    page_size: PageSize = 40,
) -> dict:
    with get_connection() as connection:
        items, total = search_repository.search(connection, query, page, page_size)
    return _page(items, page, page_size, total)


@router.post(
    "/generator/run",
    response_model=GenerationAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def run_generator(
    payload: GenerateTransactionsRequest,
    background_tasks: BackgroundTasks,
) -> GenerationAccepted:
    """Run the former app.main load-generator behavior without blocking HTTP."""
    background_tasks.add_task(
        FraudMonitoringApp().enqueue_generated_transactions,
        payload.valid_count,
        payload.invalid_count,
        payload.fraud_count,
    )
    return GenerationAccepted(
        transaction_count=(
            payload.valid_count + payload.invalid_count + payload.fraud_count
        )
    )
