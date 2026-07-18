from unittest.mock import Mock

from app.producer.transaction_producer import TransactionProducer
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
