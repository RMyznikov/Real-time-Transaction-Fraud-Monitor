"""Database operations for fraud alerts."""

from app.models.fraud_alert import FraudAlert
from db.database import get_connection


def create(alert: FraudAlert) -> None:
    """Insert a fraud alert received from the caller."""
    with get_connection() as connection:
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


def get(transaction_id: str, rule: str) -> FraudAlert | None:
    """Find an alert by the unique transaction_id and rule pair."""
    with get_connection() as connection:
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


def get_all() -> list[FraudAlert]:
    """Return all fraud alerts, newest alerts first."""
    with get_connection() as connection:
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


def update(alert: FraudAlert) -> bool:
    """Update an alert and report whether a row was found."""
    with get_connection() as connection:
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


def delete(transaction_id: str, rule: str) -> bool:
    """Delete an alert and report whether a row was deleted."""
    with get_connection() as connection:
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
