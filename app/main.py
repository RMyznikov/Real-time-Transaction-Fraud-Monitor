from app.consumer.kafka_fraud_consumer import KafkaFraudConsumer
from app.producer.kafka_transaction_producer import KafkaTransactionProducer
from app.producer.transaction_producer import TransactionProducer
from app.services.transaction_processing_service import TransactionProcessingService


class FraudMonitoringApp:
    def __init__(self) -> None:
        self.t_producer = TransactionProducer()
        self.t_processor = TransactionProcessingService()
        self.kafka_t_producer = KafkaTransactionProducer()
        self.kafka_fraud_consumer = KafkaFraudConsumer()


    def localFraudMonitoring(self) -> None:
        transactions = self.t_producer.produce_transactions(10, 10, 10)
        self.t_processor.process_transactions(transactions)


    def main(self) -> None:
        transactions = self.t_producer.produce_transactions(10, 10, 10)

        for transaction in transactions:
            self.kafka_t_producer.send(transaction)

        self.kafka_t_producer.flush()

        self.kafka_fraud_consumer.consume()



if __name__ == "__main__":
    fmApp = FraudMonitoringApp()
    fmApp.main()
