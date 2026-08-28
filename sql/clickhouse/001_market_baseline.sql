CREATE DATABASE IF NOT EXISTS market_intelligence;

CREATE TABLE IF NOT EXISTS market_intelligence.market_ticker (
    exchange String,
    symbol String,
    price Float64,
    change_24h Float64,
    volume_24h Float64,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, symbol, timestamp);

CREATE TABLE IF NOT EXISTS market_intelligence.market_kline (
    exchange String,
    symbol String,
    interval String,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,
    quote_volume Float64,
    timestamp DateTime,
    created_at DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, symbol, interval, timestamp);

CREATE TABLE IF NOT EXISTS market_intelligence.market_trade (
    exchange String,
    symbol String,
    trade_id String,
    price Float64,
    quantity Float64,
    side String,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, symbol, timestamp);

CREATE TABLE IF NOT EXISTS market_intelligence.funding_rate_history (
    exchange String,
    symbol String,
    funding_rate Float64,
    next_funding_time DateTime,
    funding_time DateTime,
    source String DEFAULT ''
) ENGINE = MergeTree
PARTITION BY toYYYYMM(funding_time)
ORDER BY (exchange, symbol, funding_time);

CREATE TABLE IF NOT EXISTS market_intelligence.open_interest_history (
    exchange String,
    symbol String,
    open_interest Float64,
    change_rate Float64,
    timestamp DateTime,
    source String DEFAULT ''
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, symbol, timestamp);

CREATE TABLE IF NOT EXISTS market_intelligence.liquidation_history (
    exchange String,
    symbol String,
    side String,
    price Float64,
    quantity Float64,
    value Float64,
    timestamp DateTime,
    source String DEFAULT ''
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, symbol, timestamp, side);

CREATE TABLE IF NOT EXISTS market_intelligence.feature_history (
    exchange String,
    symbol String,
    feature_name String,
    feature_value Float64,
    version String,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, symbol, feature_name, timestamp);

CREATE TABLE IF NOT EXISTS market_intelligence.score_history (
    exchange String,
    symbol String,
    score_type String,
    score Float64,
    confidence Float64 DEFAULT 0,
    model_version String DEFAULT '',
    opportunity_score Float64 DEFAULT 0,
    risk_score Float64 DEFAULT 0,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, symbol, score_type, timestamp);

CREATE TABLE IF NOT EXISTS market_intelligence.prediction_history (
    exchange String,
    symbol String,
    model_name String,
    model_version String,
    opportunity_score Float64,
    risk_score Float64,
    confidence Float64,
    overall_score Float64,
    prediction Float64,
    risk_warning String,
    factors String,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, symbol, model_name, model_version, timestamp);

CREATE TABLE IF NOT EXISTS market_intelligence.ranking_history (
    exchange String,
    symbol String,
    ranking_type String,
    rank UInt32,
    score Float64,
    confidence Float64,
    model_version String,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, ranking_type, timestamp, rank);

CREATE TABLE IF NOT EXISTS market_intelligence.ranking_factor_contribution (
    exchange String,
    symbol String,
    ranking_type String,
    factor String,
    factor_value Float64,
    weight Float64,
    contribution Float64,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, symbol, ranking_type, factor, timestamp);

CREATE TABLE IF NOT EXISTS market_intelligence.ranking_monitor_event (
    exchange String,
    symbol String,
    ranking_type String,
    event_action String,
    from_rank UInt32 DEFAULT 0,
    to_rank UInt32 DEFAULT 0,
    score Float64 DEFAULT 0,
    previous_score Float64 DEFAULT 0,
    score_change Float64 DEFAULT 0,
    market_bias String DEFAULT '',
    summary String DEFAULT '',
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, ranking_type, event_action, timestamp, symbol);

CREATE TABLE IF NOT EXISTS market_intelligence.signal_history (
    signal_id String,
    exchange String,
    symbol String,
    signal_type String,
    score Float64,
    confidence Float64,
    reason String,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (exchange, symbol, signal_type, timestamp);

CREATE TABLE IF NOT EXISTS market_intelligence.event_dead_letter (
    event_type String,
    source String,
    reason String,
    payload String,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (event_type, source, timestamp);
