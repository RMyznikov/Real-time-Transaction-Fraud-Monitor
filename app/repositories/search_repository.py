"""Cross-entity search queries used by the monitoring web API."""

from typing import Any

import psycopg


def search(
    connection: psycopg.Connection,
    query: str,
    page: int = 1,
    page_size: int = 40,
) -> tuple[list[dict[str, Any]], int]:
    """Search transactions and alerts as one chronologically ordered result set."""
    pattern = f"%{query.strip().lower()}%"
    parameters = (pattern, pattern)
    union_sql = f"""
        SELECT
            'transaction'::text AS result_type,
            transaction_id,
            account_id,
            amount,
            currency::text,
            country::text,
            NULL::text AS rule,
            NULL::integer AS risk_score,
            transaction_time AS occurred_at
        FROM transactions
        WHERE search_text LIKE %s

        UNION ALL

        SELECT
            'fraud_alert'::text AS result_type,
            transaction_id,
            account_id,
            NULL::numeric AS amount,
            NULL::text AS currency,
            NULL::text AS country,
            rule,
            risk_score,
            created_at AS occurred_at
        FROM fraud_alerts
        WHERE search_text LIKE %s
    """

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM ({union_sql}) AS matches", parameters)
        total = cursor.fetchone()[0]
        cursor.execute(
            f"""
            SELECT result_type, transaction_id, account_id, amount, currency,
                   country, rule, risk_score, occurred_at
            FROM ({union_sql}) AS matches
            ORDER BY occurred_at DESC, result_type, transaction_id
            LIMIT %s OFFSET %s
            """,
            (*parameters, page_size, (page - 1) * page_size),
        )
        rows = cursor.fetchall()

    keys = (
        "result_type",
        "transaction_id",
        "account_id",
        "amount",
        "currency",
        "country",
        "rule",
        "risk_score",
        "occurred_at",
    )
    return [dict(zip(keys, row, strict=True)) for row in rows], total
