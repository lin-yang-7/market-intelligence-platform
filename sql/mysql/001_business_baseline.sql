CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(64) NOT NULL DEFAULT 'user',
    plan VARCHAR(64) NOT NULL DEFAULT 'free',
    status VARCHAR(32) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_users_email (email),
    KEY idx_users_status (status)
);

CREATE TABLE IF NOT EXISTS api_keys (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL,
    api_key VARCHAR(128) NOT NULL,
    secret_hash VARCHAR(255) NOT NULL,
    scopes JSON NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    expires_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_api_keys_api_key (api_key),
    KEY idx_api_keys_user_id (user_id)
);

CREATE TABLE IF NOT EXISTS alert_rules (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL,
    rule_type VARCHAR(64) NOT NULL,
    conditions JSON NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(32) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    KEY idx_alert_rules_user_id (user_id),
    KEY idx_alert_rules_enabled (enabled)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    plan_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    started_at DATETIME NOT NULL,
    renews_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    KEY idx_subscriptions_user_id (user_id),
    KEY idx_subscriptions_status (status)
);

CREATE TABLE IF NOT EXISTS usage_counters (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    plan_id VARCHAR(64) NOT NULL,
    metric VARCHAR(80) NOT NULL,
    amount BIGINT NOT NULL,
    period_start DATETIME NOT NULL,
    period_end DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    KEY idx_usage_user_metric (user_id, metric),
    KEY idx_usage_period (period_start, period_end)
);

CREATE TABLE IF NOT EXISTS invoices (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    subscription_id BIGINT NULL,
    invoice_no VARCHAR(128) NOT NULL,
    amount_cents BIGINT NOT NULL,
    currency VARCHAR(16) NOT NULL DEFAULT 'USD',
    status VARCHAR(32) NOT NULL,
    issued_at DATETIME NOT NULL,
    paid_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_invoices_invoice_no (invoice_no),
    KEY idx_invoices_user_status (user_id, status)
);

CREATE TABLE IF NOT EXISTS payment_events (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    invoice_id BIGINT NULL,
    provider VARCHAR(64) NOT NULL,
    provider_event_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL,
    payload JSON NOT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY uk_payment_provider_event (provider, provider_event_id),
    KEY idx_payment_events_user_id (user_id)
);

CREATE TABLE IF NOT EXISTS model_versions (
    id BIGINT PRIMARY KEY,
    model_name VARCHAR(128) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    strategy VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    metadata JSON NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_model_version (model_name, model_version),
    KEY idx_model_versions_status (status)
);

CREATE TABLE IF NOT EXISTS notification_deliveries (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    channel VARCHAR(32) NOT NULL,
    dedupe_key VARCHAR(255) NULL,
    title VARCHAR(255) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    error_message VARCHAR(500) NULL,
    attempts INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    KEY idx_notification_user_status (user_id, status),
    KEY idx_notification_dedupe_key (dedupe_key)
);
