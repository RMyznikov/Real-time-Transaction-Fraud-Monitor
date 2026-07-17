"""Database operations for transactions.

The caller owns the connection and decides when to commit or roll back.
"""

import psycopg

from app.models.transaction import Transaction


def create(connection: psycopg.Connection, transaction: Transaction) -> None:
    """Insert a transaction received from the caller."""
    with connection.cursor() as cursor:
        # %s placeholders keep values separate from SQL and prevent SQL injection.
        cursor.execute(
            """
            INSERT INTO transactions (
                transaction_id,
                account_id,
                amount,
                currency,
                country,
                transaction_time
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                transaction.transaction_id,
                transaction.account_id,
                transaction.amount,
                transaction.currency,
                transaction.country,
                transaction.timestamp,
            ),
        )


def get_by_id(
    connection: psycopg.Connection,
    transaction_id: str,
) -> Transaction | None:
    """Return one transaction, or None when it does not exist."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT transaction_id, account_id, amount, currency, country,
                   transaction_time
            FROM transactions
            WHERE transaction_id = %s
            """,
            (transaction_id,),
        )
        row = cursor.fetchone()

    return _to_transaction(row) if row else None


def get_all(connection: psycopg.Connection) -> list[Transaction]:
    """Return all transactions, newest transactions first."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT transaction_id, account_id, amount, currency, country,
                   transaction_time
            FROM transactions
            ORDER BY transaction_time DESC
            """
        )
        rows = cursor.fetchall()

    return [_to_transaction(row) for row in rows]


def update(connection: psycopg.Connection, transaction: Transaction) -> bool:
    """Update a transaction and report whether a row was found."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE transactions
            SET account_id = %s,
                amount = %s,
                currency = %s,
                country = %s,
                transaction_time = %s
            WHERE transaction_id = %s
            """,
            (
                transaction.account_id,
                transaction.amount,
                transaction.currency,
                transaction.country,
                transaction.timestamp,
                transaction.transaction_id,
            ),
        )
        # rowcount is 1 when UPDATE found the transaction, otherwise 0.
        return cursor.rowcount > 0


def delete(connection: psycopg.Connection, transaction_id: str) -> bool:
    """Delete a transaction and report whether a row was deleted."""
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM transactions WHERE transaction_id = %s",
            (transaction_id,),
        )
        return cursor.rowcount > 0


def _to_transaction(row: tuple) -> Transaction:
    """Convert a database row into the application model."""
    return Transaction(
        transaction_id=row[0],
        account_id=row[1],
        amount=row[2],
        currency=row[3],
        country=row[4],
        timestamp=row[5],
    )
