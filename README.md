# Real-time Transaction Fraud Monitor

Навчальна event-driven система для моніторингу фінансових транзакцій у реальному часі. Застосунок приймає транзакції через Kafka, валідує їх, перевіряє fraud-правила та зберігає транзакції і fraud alerts у PostgreSQL.

Проєкт демонструє:

- event-driven архітектуру з Apache Kafka;
- паралельну обробку подій кількома workers і consumers;
- transactional outbox pattern;
- атомарне збереження business-даних і вихідних подій;
- ручне commit Kafka offset після обробки повідомлення;
- Docker Compose deployment з health checks і керованим порядком запуску.

## Архітектура

```text
Load Generator
      |
      v
PostgreSQL Outbox
      |
      v
Outbox Workers (3) ---> Kafka: transactions (3 partitions)
                              |
                              v
                       Fraud Consumers (3)
                              |
                              v
                  PostgreSQL: transactions
                              |
                              v
                  PostgreSQL: fraud_alerts
                              |
                              v
                   Outbox ---> Kafka: fraud-alerts
```

### Потік обробки

1. One-shot сервіс `load-generator` запускає `app.main` і створює тестові транзакції.
2. Події `TRANSACTION_CREATED` записуються у таблицю `outbox_events`.
3. Три `outbox-worker` читають неопубліковані події через `FOR UPDATE SKIP LOCKED` і надсилають їх у Kafka.
4. Три `fraud-consumer` працюють в одній consumer group. Kafka розподіляє між ними три партиції topic `transactions`.
5. Consumer валідує подію, зберігає транзакцію та запускає fraud detection.
6. Fraud alert і подія `FRAUD_ALERT_CREATED` зберігаються в одній транзакції PostgreSQL.
7. Outbox worker публікує fraud alert у topic `fraud-alerts`.

## Fraud-правило

Поточне правило виявляє транзакції з великою сумою:

| Умова | Alert | Risk score |
| --- | --- | ---: |
| `amount >= 10000` | `HIGH_AMOUNT` | `80` |

Архітектура дозволяє додавати нові правила в `FraudRuleChecker` без зміни Kafka consumer.

## Модель даних

### `transactions`

Зберігає ID транзакції, акаунт, суму, валюту, країну, час транзакції та час обробки.

### `fraud_alerts`

Зберігає посилання на транзакцію, fraud-правило, risk score і час створення. Комбінація `transaction_id + rule` є унікальною.

### `outbox_events`

Містить UUID події, topic, event type, key, JSON payload, час створення і час публікації.

## Docker-сервіси

| Сервіс | Кількість | Призначення |
| --- | ---: | --- |
| `postgres` | 1 | Зберігання business-даних і outbox |
| `db-init` | 1, one-shot | Повторне безпечне застосування SQL-схеми та індексів |
| `kafka` | 1 | Kafka broker |
| `kafka-init` | 1, one-shot | Створення topics з трьома партиціями |
| `load-generator` | 1, one-shot | Тестове навантаження |
| `outbox-worker` | 3 | Доставка outbox-подій у Kafka |
| `fraud-consumer` | 3 | Обробка транзакцій |
| `web-server` | 1 | FastAPI REST API на `localhost:8080` |

One-shot сервіси після успішного виконання мають статус `Exited (0)`. Це очікувана поведінка.

## Тестове навантаження

За замовчуванням `app.main` створює:

- 10000 валідних транзакцій із сумою нижче fraud-ліміту;
- 10000 невалідних транзакцій із нульовою сумою;
- 10000 fraud-транзакцій із сумою від fraud-ліміту.

Невалідні події пропускаються після валідації. `load-generator` не перезапускається після завершення, але виконається знову при recreate deployment.

## Вимоги

- Docker Desktop або Docker Engine;
- Docker Compose;
- Python 3.13 — тільки для запуску без Docker чи unit-тестів.

## Запуск

З кореня проєкту:

```powershell
docker compose up --build -d
```

Команда збирає application image і запускає PostgreSQL, Kafka, init-сервіси, FastAPI web-server, три workers і три consumers.

REST API доступний на `http://localhost:8080`, інтерактивна Swagger-документація — на `http://localhost:8080/docs`.

### REST API

| Метод | Endpoint | Призначення |
| --- | --- | --- |
| `GET/POST` | `/api/transactions` | Список або створення транзакції |
| `GET/PUT/DELETE` | `/api/transactions/{transaction_id}` | CRUD однієї транзакції |
| `GET/POST` | `/api/fraud-alerts` | Список або створення fraud alert |
| `GET/PUT/DELETE` | `/api/fraud-alerts/{transaction_id}/{rule}` | CRUD одного fraud alert |
| `GET` | `/api/search?query=...` | Наскрізний пошук по транзакціях та alerts |
| `POST` | `/api/generator/run` | Асинхронний запуск генератора подій |

Списки приймають `page`, `page_size` і `search`. Значення `page_size` за замовчуванням — `40`, максимальне — `100`. Пошук, `COUNT`, сортування та пагінація виконуються у PostgreSQL; для текстових полів створені trigram GIN-індекси.

Перевірити стан усіх контейнерів:

```powershell
docker compose ps --all
```

Переглянути логи:

```powershell
docker compose logs -f
```

Логи окремих ролей:

```powershell
docker compose logs -f load-generator
docker compose logs -f outbox-worker
docker compose logs -f fraud-consumer
```

Зупинити deployment зі збереженням PostgreSQL і Kafka volumes:

```powershell
docker compose down
```

Видалити deployment разом із локальними даними:

```powershell
docker compose down --volumes
```

> `down --volumes` безповоротно видаляє PostgreSQL і Kafka volumes.

## Конфігурація

Додаток читає налаштування з environment variables:

| Змінна | Призначення |
| --- | --- |
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port |
| `DB_NAME` | Назва бази |
| `DB_USER` | PostgreSQL user |
| `DB_PASSWORD` | PostgreSQL password |
| `KAFKA_URL` | Kafka bootstrap servers |
| `KAFKA_TOPIC` | Topic вхідних транзакцій |
| `KAFKA_GROUP_ID` | Consumer group ID |
| `OUTBOX_POLL_INTERVAL_SECONDS` | Інтервал опитування outbox |
| `OUTBOX_BATCH_SIZE` | Максимальна кількість подій в одній пачці |
| `WEB_EXTERNAL_PORT` | Зовнішній порт web-server у registry Compose, типово `8080` |

Для production environment облікові дані слід передавати через secret manager або deployment environment, а не зберігати в репозиторії.

## Віддалений запуск без коду

На віддаленій машині потрібні лише:

```text
.env
docker-compose.registry.yml
```

Python-код, `Dockerfile`, `requirements.txt`, `db/schema.sql` і `scripts/` не потрібні. Application image містить код і SQL-схему, а remote Compose сам створює Kafka topics.

### `.env`

```dotenv
APP_IMAGE=ghcr.io/rmyznikov/real-time-transaction-fraud-monitor:v1
POSTGRES_DB=fraud_monitoring
POSTGRES_USER=fraud_app
POSTGRES_PASSWORD=change-this-password
POSTGRES_EXTERNAL_PORT=5432
KAFKA_EXTERNAL_PORT=9092
OUTBOX_POLL_INTERVAL_SECONDS=1
OUTBOX_BATCH_SIZE=100
```

Пароль `change-this-password` потрібно замінити перед запуском. `.env` не слід додавати в Git.

### `docker-compose.registry.yml`

Повний remote Compose вже доданий до проєкту як `docker-compose.registry.yml`. Він не містить `build` або bind mounts на файли з репозиторію та описує повний deployment:

```yaml
name: fraud-monitoring

x-app-environment: &app-environment
  DB_HOST: postgres
  DB_PORT: 5432
  DB_NAME: ${POSTGRES_DB:-fraud_monitoring}
  DB_USER: ${POSTGRES_USER:-fraud_app}
  DB_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}

x-app-dependencies: &app-dependencies
  postgres:
    condition: service_healthy
  db-init:
    condition: service_completed_successfully
  kafka:
    condition: service_healthy
  kafka-init:
    condition: service_completed_successfully

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-fraud_monitoring}
      POSTGRES_USER: ${POSTGRES_USER:-fraud_app}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}
    ports:
      - "${POSTGRES_EXTERNAL_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 10
    volumes:
      - postgres_data:/var/lib/postgresql/data

  db-init:
    image: ${APP_IMAGE}
    command:
      - python
      - -c
      - |
        from pathlib import Path
        from db.database import get_connection

        with get_connection() as connection:
            connection.execute(Path("/app/db/schema.sql").read_text())
    environment:
      <<: *app-environment
    depends_on:
      postgres:
        condition: service_healthy
    restart: "no"

  kafka:
    image: apache/kafka:latest
    ports:
      - "${KAFKA_EXTERNAL_PORT:-9092}:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: INTERNAL://0.0.0.0:29092,EXTERNAL://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka:29092,EXTERNAL://localhost:${KAFKA_EXTERNAL_PORT:-9092}
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_NUM_PARTITIONS: 3
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:29092 --list"]
      interval: 5s
      timeout: 10s
      retries: 12
      start_period: 10s
    volumes:
      - kafka_data:/var/lib/kafka/data

  kafka-init:
    image: apache/kafka:latest
    command:
      - /bin/sh
      - -ec
      - |
        for topic in transactions fraud-alerts; do
          /opt/kafka/bin/kafka-topics.sh \
            --bootstrap-server kafka:29092 \
            --create \
            --if-not-exists \
            --topic "$$topic" \
            --partitions 3 \
            --replication-factor 1
        done
    depends_on:
      kafka:
        condition: service_healthy
    restart: "no"

  load-generator:
    image: ${APP_IMAGE}
    command: ["python", "-m", "app.main"]
    environment:
      <<: *app-environment
    depends_on:
      <<: *app-dependencies
    restart: "no"

  outbox-worker:
    image: ${APP_IMAGE}
    command: ["python", "-m", "app.workers.outbox_worker"]
    environment:
      <<: *app-environment
      KAFKA_URL: kafka:29092
      OUTBOX_POLL_INTERVAL_SECONDS: ${OUTBOX_POLL_INTERVAL_SECONDS:-1}
      OUTBOX_BATCH_SIZE: ${OUTBOX_BATCH_SIZE:-100}
    depends_on:
      <<: *app-dependencies
    deploy:
      replicas: 3
    restart: unless-stopped

  fraud-consumer:
    image: ${APP_IMAGE}
    command: ["python", "-m", "app.consumer.kafka_fraud_consumer"]
    environment:
      <<: *app-environment
      KAFKA_URL: kafka:29092
      KAFKA_TOPIC: transactions
      KAFKA_GROUP_ID: fraud-monitor
    depends_on:
      <<: *app-dependencies
    deploy:
      replicas: 3
    restart: unless-stopped

volumes:
  postgres_data:
  kafka_data:
```

### Запуск на віддаленій машині

Якщо GHCR package приватний, спочатку потрібно виконати `docker login ghcr.io`. Після цього:

```powershell
docker compose --env-file .env -f docker-compose.registry.yml pull
docker compose --env-file .env -f docker-compose.registry.yml up -d
```

Перевірити контейнери:

```powershell
docker compose --env-file .env -f docker-compose.registry.yml ps --all
```

Зупинити deployment:

```powershell
docker compose --env-file .env -f docker-compose.registry.yml down
```

## Структура проєкту

```text
app/
|-- consumer/       Kafka consumers
|-- mappers/        JSON/payload <-> domain models
|-- models/         Transaction, FraudAlert, OutboxEvent
|-- producer/       Test data and Kafka producers
|-- repositories/   PostgreSQL access layer
|-- services/       Validation, fraud rules and processing
|-- workers/        Transactional outbox worker
`-- main.py         Test load entry point

db/
|-- database.py     PostgreSQL connection factory
`-- schema.sql      Database schema

scripts/
`-- create-kafka-topics.sh

tests/              Unit tests
Dockerfile          Application image
docker-compose.yml  Local deployment
docker-compose.registry.yml  Remote deployment without source code
requirements.txt    Python dependencies
```

## Тести

Встановити залежності та запустити unit-тести:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

Тести покривають:

- генерацію транзакцій;
- валідацію і mapping;
- fraud detection;
- transaction processing service;
- repositories і transactional outbox;
- Kafka producers і consumer behavior.

## Обмеження demo deployment

- Kafka працює як single broker з replication factor `1`.
- Fraud detection містить одне демонстраційне правило.
- `load-generator` автоматично запускається при створенні deployment.
- Перед production deployment потрібно винести secrets з Compose, налаштувати Kafka replication, monitoring, dead-letter handling і retention policies.
