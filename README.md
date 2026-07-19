# Real-time Transaction Fraud Monitor

Система отримує транзакції як події, обробляє їх паралельно, перевіряє правила ризику та створює fraud alerts.

## Запуск у Docker

Весь стенд збирається та запускається однією командою:

```shell
docker compose up --build -d
```

Будуть запущені PostgreSQL, Kafka, ініціалізація Kafka-топіків, 3 outbox-воркери та 3 fraud-консюмери.

Перевірити стан:

```shell
docker compose ps
```

Зупинити стенд:

```shell
docker compose down
```
