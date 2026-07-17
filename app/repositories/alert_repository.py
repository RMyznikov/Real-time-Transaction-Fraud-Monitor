"""Database operations for fraud alerts.

The caller owns the connection and decides when to commit or roll back.
"""

import psycopg

from app.models.fraud_alert import FraudAlert


def create(connection: psycopg.Connection, alert: FraudAlert) -> None:
    """Insert a fraud alert received from the caller."""
    with connection.cursor() as cursor:
        # Values are passed separately so user input never becomes SQL code.
        cursor.execute(
            """
            INSERT INTO fraud_alerts (
                transaction_id,
                account_id,
                rule,
                risk_score,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                alert.transaction_id,
                alert.account_id,
                alert.rule,
                alert.risk_score,
                alert.created_at,
            ),
        )


def create_many(
    connection: psycopg.Connection,
    alerts: list[FraudAlert],
) -> None:
    """Insert multiple fraud alerts in one database transaction."""
    if not alerts:
        # An empty list has nothing to save.
        return

    values = [
        (
            alert.transaction_id,
            alert.account_id,
            alert.rule,
            alert.risk_score,
            alert.created_at,
        )
        for alert in alerts
    ]

    with connection.cursor() as cursor:
        # executemany runs the same parameterized INSERT for every alert.
        cursor.executemany(
            """
            INSERT INTO fraud_alerts (
                transaction_id,
                account_id,
                rule,
                risk_score,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            values,
        )


def get(
    connection: psycopg.Connection,
    transaction_id: str,
    rule: str,
) -> FraudAlert | None:
    """Find an alert by the unique transaction_id and rule pair."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT transaction_id, account_id, rule, risk_score, created_at
            FROM fraud_alerts
            WHERE transaction_id = %s AND rule = %s
            """,
            (transaction_id, rule),
        )
        row = cursor.fetchone()

    return _to_fraud_alert(row) if row else None


def get_all(connection: psycopg.Connection) -> list[FraudAlert]:
    """Return all fraud alerts, newest alerts first."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT transaction_id, account_id, rule, risk_score, created_at
            FROM fraud_alerts
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()

    return [_to_fraud_alert(row) for row in rows]


def update(connection: psycopg.Connection, alert: FraudAlert) -> bool:
    """Update an alert and report whether a row was found."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE fraud_alerts
            SET account_id = %s,
                risk_score = %s,
                created_at = %s
            WHERE transaction_id = %s AND rule = %s
            """,
            (
                alert.account_id,
                alert.risk_score,
                alert.created_at,
                alert.transaction_id,
                alert.rule,
            ),
        )
        return cursor.rowcount > 0


def delete(
    connection: psycopg.Connection,
    transaction_id: str,
    rule: str,
) -> bool:
    """Delete an alert and report whether a row was deleted."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM fraud_alerts
            WHERE transaction_id = %s AND rule = %s
            """,
            (transaction_id, rule),
        )
        return cursor.rowcount > 0


def _to_fraud_alert(row: tuple) -> FraudAlert:
    """Convert a database row into the application model."""
    return FraudAlert(
        transaction_id=row[0],
        account_id=row[1],
        rule=row[2],
        risk_score=row[3],
        created_at=row[4],
    )
