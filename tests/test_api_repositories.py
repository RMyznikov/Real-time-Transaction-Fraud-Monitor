from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from app.repositories import alert_repository, search_repository, transaction_repository


def make_connection() -> tuple[MagicMock, MagicMock]:
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    return connection, cursor


def test_transaction_page_searches_and_paginates_in_database() -> None:
    connection, cursor = make_connection()
    timestamp = datetime.now(timezone.utc)
    cursor.fetchone.return_value = (81,)
    cursor.fetchall.return_value = [
        ("tx-1", "acc-7", Decimal("12.50"), "UAH", "UA", timestamp)
    ]

    items, total = transaction_repository.get_page(
        connection,
        page=3,
        page_size=40,
        search=" ACC-7 ",
    )

    assert total == 81
    assert items[0].transaction_id == "tx-1"
    query_parameters = cursor.execute.call_args_list[1].args[1]
    assert query_parameters == (
        "%acc-7%",
        "%acc-7%",
        40,
        80,
    )


def test_alert_page_defaults_to_forty_items() -> None:
    connection, cursor = make_connection()
    cursor.fetchone.return_value = (0,)
    cursor.fetchall.return_value = []

    items, total = alert_repository.get_page(connection)

    assert items == []
    assert total == 0
    assert cursor.execute.call_args_list[1].args[1][-2:] == (40, 0)


def test_global_search_uses_one_offset_across_both_entity_types() -> None:
    connection, cursor = make_connection()
    cursor.fetchone.return_value = (50,)
    cursor.fetchall.return_value = []

    _, total = search_repository.search(connection, "tx-10", page=2, page_size=40)

    assert total == 50
    query_parameters = cursor.execute.call_args_list[1].args[1]
    assert query_parameters[-2:] == (40, 40)
    assert query_parameters[:-2] == ("%tx-10%",) * 2
