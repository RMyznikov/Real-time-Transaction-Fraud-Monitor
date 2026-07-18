from app.producer.transaction_producer import TransactionProducer
from app.services.transaction_processing_service import TransactionProcessingService


class FraudMonitoringApp:
    def __init__(self) -> None:
        self.t_producer = TransactionProducer()
        self.t_processor = TransactionProcessingService()

    def main(self) -> None:
        transactions = self.t_producer.produce_transactions(10, 10, 10)
        self.t_processor.process_transactions(transactions)


if __name__ == "__main__":
    fmApp = FraudMonitoringApp()
    fmApp.main()
