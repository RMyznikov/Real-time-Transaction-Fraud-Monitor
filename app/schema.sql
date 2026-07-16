CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR PRIMARY KEY,
    account_id VARCHAR NOT NULL,
    amount NUMERIC(18, 2) NOT NULL CHECK (amount > 0),
    currency CHAR(3) NOT NULL,
    country CHAR(2) NOT NULL,
    transaction_time TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE TABLE IF NOT EXISTS fraud_alerts (
    id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR NOT NULL,
    account_id VARCHAR NOT NULL,
    rule VARCHAR NOT NULL,
    risk_score INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (transaction_id, rule),
    CONSTRAINT fk_fraud_alerts_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions (transaction_id) ON DELETE CASCADE
);
