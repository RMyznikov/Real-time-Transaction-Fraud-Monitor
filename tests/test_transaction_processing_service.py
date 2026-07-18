from unittest.mock import MagicMock, Mock, patch

from app.enums import EventType, KafkaTopic
from app.producer.transaction_producer import TransactionProducer
from app.repositories.outbox_repository import OutboxRepository
from app.services.transaction_processing_service import TransactionProcessingService


def test_process_transactions_continues_after_invalid_transaction() -> None:
    producer = TransactionProducer()
    transactions = producer.produce_transactions(1, 1, 1)
    service = TransactionProcessingService()
    validation_error = ValueError("amount must be greater than zero")
    service.process_transaction = Mock(
        side_effect=[None, validation_error, None],
    )

    errors = service.process_transactions(transactions)

    assert service.process_transaction.call_count == 3
    assert errors == [(transactions[1], validation_error)]


def test_fraud_alert_and_outbox_event_use_same_db_transaction() -> None:
    transaction = TransactionProducer().produce_fraud_transaction()
    connection = MagicMock()
    connection.__enter__.return_value = connection
    service = TransactionProcessingService()

    with (
        patch(
            "app.services.transaction_processing_service.get_connection",
            return_value=connection,
        ),
        patch(
            "app.services.transaction_processing_service.transaction_repository.create"
        ) as create_transaction,
        patch(
            "app.services.transaction_processing_service.alert_repository.create_many"
        ) as create_alerts,
        patch.object(OutboxRepository, "create") as create_outbox_event,
    ):
        alerts = service.process_transaction(transaction)

    alert = alerts[0]
    create_transaction.assert_called_once_with(connection, transaction)
    create_alerts.assert_called_once_with(connection, alerts)
    assert create_outbox_event.call_args.kwargs["connection"] is connection
    assert create_outbox_event.call_args.kwargs["topic"] is KafkaTopic.FRAUD_ALERTS
    assert (
        create_outbox_event.call_args.kwargs["event_type"]
        is EventType.FRAUD_ALERT_CREATED
    )
    assert create_outbox_event.call_args.kwargs["event_key"] == alert.account_id
