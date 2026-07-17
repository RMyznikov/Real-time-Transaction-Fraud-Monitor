"""Database connection and session configuration."""
import os
from datetime import datetime, timezone
from decimal import Decimal
import psycopg
from dotenv import load_dotenv

load_dotenv()

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')


def get_connection() -> psycopg.Connection:
    return psycopg.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
    )


def test_queries():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions (transaction_id, account_id, amount, currency, country, transaction_time)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                ("tx-1001", "acc-50", Decimal("1.00"), 'USD', 'UA', datetime.now(timezone.utc)), )

            cur.execute("SELECT * FROM transactions")
            print(cur.fetchone())
