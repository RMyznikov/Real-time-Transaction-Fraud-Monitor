from unittest.mock import MagicMock, patch

from fastapi import BackgroundTasks

from app.api.router import list_transactions, run_generator
from app.api.schemas import GenerateTransactionsRequest
from app.web_server import app
from app.web_server import health


def test_health_endpoint() -> None:
    assert health().model_dump() == {"status": "ok"}
    assert "/health" in app.openapi()["paths"]


def test_transaction_list_defaults_to_first_page_of_forty() -> None:
    connection = MagicMock()
    connection.__enter__.return_value = connection

    with (
        patch("app.api.router.get_connection", return_value=connection),
        patch(
            "app.api.router.transaction_repository.get_page",
            return_value=([], 0),
        ) as get_page,
    ):
        response = list_transactions()

    assert response == {
        "items": [],
        "page": 1,
        "page_size": 40,
        "total": 0,
        "total_pages": 0,
    }
    get_page.assert_called_once_with(connection, 1, 40, None)


def test_generator_endpoint_schedules_main_generation_behavior() -> None:
    background_tasks = BackgroundTasks()
    payload = GenerateTransactionsRequest(
        valid_count=2,
        invalid_count=1,
        fraud_count=3,
    )

    with patch("app.api.router.FraudMonitoringApp") as app_class:
        response = run_generator(payload, background_tasks)

    assert response.model_dump() == {"status": "accepted", "transaction_count": 6}
    assert len(background_tasks.tasks) == 1
    task = background_tasks.tasks[0]
    assert task.func == app_class.return_value.enqueue_generated_transactions
    assert task.args == (2, 1, 3)
