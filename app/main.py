from app.producer.transaction_producer import TransactionProducer
from app.services.transaction_processing_service import TransactionProcessingService


class FraudMonitoringApp:
    def __init__(self) -> None:
        self.tProducer = TransactionProducer()
        self.tProcessor = TransactionProcessingService()

    def main(self) -> None:
        transactions = self.tProducer.produce_transactions(10, 10, 10)
        self.tProcessor.process_transactions(transactions)


if __name__ == "__main__":
    fmApp = FraudMonitoringApp()
    fmApp.main()
