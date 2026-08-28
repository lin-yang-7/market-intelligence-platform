# ClickHouse Table Design

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the ClickHouse table design for analytical and
time-series data in the Market Intelligence Platform.

The design focuses on:

-   High ingestion speed
-   Fast analytical queries
-   Historical data storage
-   Quantitative research support

------------------------------------------------------------------------

# 2. Design Principles

All ClickHouse tables follow:

-   MergeTree family engines
-   Time-based partitioning
-   Symbol-based ordering
-   Append-oriented writes
-   Optimized analytical queries

------------------------------------------------------------------------

# 3. Market Kline Table

## Table Name

    market_kline

## Purpose

Store OHLCV historical candle data.

## Fields

  Field          Type
  -------------- ----------
  exchange       String
  symbol         String
  interval       String
  open           Float64
  high           Float64
  low            Float64
  close          Float64
  volume         Float64
  quote_volume   Float64
  timestamp      DateTime
  created_at     DateTime

## Engine

    MergeTree

## Partition

    toYYYYMM(timestamp)

## Order By

    (exchange, symbol, interval, timestamp)

------------------------------------------------------------------------

# 4. Trade History Table

## Table Name

    market_trade

## Purpose

Store transaction-level market trades.

## Fields

  Field       Type
  ----------- ----------
  exchange    String
  symbol      String
  trade_id    String
  price       Float64
  quantity    Float64
  side        String
  timestamp   DateTime

## Partition

    toYYYYMM(timestamp)

## Order By

    (exchange, symbol, timestamp)

------------------------------------------------------------------------

# 5. Funding Rate Table

## Table Name

    funding_rate_history

## Purpose

Store perpetual contract funding data.

## Fields

  Field          Type
  -------------- ----------
  exchange       String
  symbol         String
  funding_rate   Float64
  funding_time   DateTime

## Partition

    toYYYYMM(funding_time)

## Order By

    (exchange, symbol, funding_time)

------------------------------------------------------------------------

# 6. Open Interest Table

## Table Name

    open_interest_history

## Purpose

Store futures open interest changes.

## Fields

  Field           Type
  --------------- ----------
  exchange        String
  symbol          String
  open_interest   Float64
  change_rate     Float64
  timestamp       DateTime

## Partition

    toYYYYMM(timestamp)

## Order By

    (exchange, symbol, timestamp)

------------------------------------------------------------------------

# 7. Liquidation Table

## Table Name

    liquidation_history

## Purpose

Store liquidation events.

## Fields

  Field       Type
  ----------- ----------
  exchange    String
  symbol      String
  side        String
  price       Float64
  quantity    Float64
  value       Float64
  timestamp   DateTime

------------------------------------------------------------------------

# 8. Feature History Table

## Table Name

    feature_history

## Purpose

Store calculated quantitative features.

## Fields

  Field           Type
  --------------- ----------
  symbol          String
  feature_name    String
  feature_value   Float64
  version         String
  timestamp       DateTime

## Order By

    (symbol, feature_name, timestamp)

------------------------------------------------------------------------

# 9. Score History Table

## Table Name

    score_history

## Purpose

Store ranking and scoring results.

## Fields

  Field        Type
  ------------ ----------
  symbol       String
  score_type   String
  score        Float64
  timestamp    DateTime

------------------------------------------------------------------------

# 10. Signal History Table

## Table Name

    signal_history

## Purpose

Store generated market signals.

## Fields

  Field         Type
  ------------- ----------
  signal_id     String
  symbol        String
  signal_type   String
  score         Float64
  confidence    Float64
  reason        String
  timestamp     DateTime

------------------------------------------------------------------------

# 11. TTL Strategy

Large historical tables may use TTL.

Example:

    timestamp + INTERVAL 5 YEAR

TTL depends on:

-   Business requirement
-   Storage cost
-   Research needs

------------------------------------------------------------------------

# 12. Data Ingestion Rules

Requirements:

-   Batch insert preferred
-   Avoid frequent updates
-   Validate before writing
-   Maintain timestamp accuracy

------------------------------------------------------------------------

# 13. Query Optimization Rules

Queries should:

-   Filter timestamp
-   Filter symbol
-   Avoid unnecessary columns
-   Use aggregation efficiently

------------------------------------------------------------------------

# 14. Future Extensions

Reserved:

-   Feature vector storage
-   AI training datasets
-   Alternative market data
-   On-chain analytics tables

------------------------------------------------------------------------

# 15. Compliance

Every ClickHouse table must define:

-   Purpose
-   Owner
-   Engine
-   Partition
-   Order key
-   Retention policy

This document defines the analytical table baseline.
