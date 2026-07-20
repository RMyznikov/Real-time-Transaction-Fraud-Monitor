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

CREATE TABLE IF NOT EXISTS outbox_events (
    id UUID PRIMARY KEY,
    topic VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    event_key VARCHAR NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

-- CREATE TABLE IF NOT EXISTS does not alter an already existing table.
-- This makes the schema file safe to reapply to a database created earlier.
ALTER TABLE outbox_events
    ADD COLUMN IF NOT EXISTS event_type VARCHAR NOT NULL DEFAULT 'unknown';

-- New events must always provide their explicit event type.
ALTER TABLE outbox_events
    ALTER COLUMN event_type DROP DEFAULT;

CREATE INDEX IF NOT EXISTS idx_outbox_events_unpublished
    ON outbox_events (created_at)
    WHERE published_at IS NULL;

-- Partial-text search is used by the web API. Trigram indexes keep searches on
-- identifiers and codes in PostgreSQL instead of loading full tables into Python.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS search_text TEXT;

CREATE OR REPLACE FUNCTION set_transaction_search_text()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.search_text := lower(concat_ws(
        ' ',
        NEW.transaction_id,
        NEW.account_id,
        NEW.amount,
        NEW.currency,
        NEW.country,
        NEW.transaction_time
    ));
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS transactions_search_text_trigger ON transactions;
CREATE TRIGGER transactions_search_text_trigger
    BEFORE INSERT OR UPDATE OF transaction_id, account_id, amount, currency,
        country, transaction_time
    ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION set_transaction_search_text();

UPDATE transactions
SET search_text = lower(concat_ws(
    ' ', transaction_id, account_id, amount, currency, country, transaction_time
))
WHERE search_text IS NULL;

ALTER TABLE transactions
    ALTER COLUMN search_text SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_transactions_search
    ON transactions USING GIN (search_text gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_transactions_time
    ON transactions (transaction_time DESC);

ALTER TABLE fraud_alerts
    ADD COLUMN IF NOT EXISTS search_text TEXT;

CREATE OR REPLACE FUNCTION set_fraud_alert_search_text()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.search_text := lower(concat_ws(
        ' ',
        NEW.transaction_id,
        NEW.account_id,
        NEW.rule,
        NEW.risk_score,
        NEW.created_at
    ));
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS fraud_alerts_search_text_trigger ON fraud_alerts;
CREATE TRIGGER fraud_alerts_search_text_trigger
    BEFORE INSERT OR UPDATE OF transaction_id, account_id, rule, risk_score, created_at
    ON fraud_alerts
    FOR EACH ROW
    EXECUTE FUNCTION set_fraud_alert_search_text();

UPDATE fraud_alerts
SET search_text = lower(concat_ws(
    ' ', transaction_id, account_id, rule, risk_score, created_at
))
WHERE search_text IS NULL;

ALTER TABLE fraud_alerts
    ALTER COLUMN search_text SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_fraud_alerts_search
    ON fraud_alerts USING GIN (search_text gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_fraud_alerts_created_at
    ON fraud_alerts (created_at DESC);
