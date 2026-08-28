# Collector Service

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the Collector Service architecture of the Market
Intelligence Platform.

Collector Service is the entry layer for external market data.

Responsibilities:

-   Connect exchanges
-   Collect real-time market data
-   Normalize data
-   Publish events
-   Maintain connection stability

------------------------------------------------------------------------

# 2. Collector Service Role

Data flow:

    Exchange

    ↓

    Collector Service

    ↓

    Kafka

    ↓

    Processing Services

Collector Service does not perform complex analysis.

Its responsibility is reliable data acquisition.

------------------------------------------------------------------------

# 3. Supported Data Sources

Initial exchanges:

-   Binance
-   OKX
-   Bybit

Future:

-   Coinbase
-   Bitget
-   Hyperliquid
-   On-chain data sources

------------------------------------------------------------------------

# 4. Supported Data Types

Collector supports:

## Market Data

-   Ticker
-   Trade
-   Kline
-   Order Book

## Derivatives Data

-   Funding Rate
-   Open Interest
-   Liquidation

------------------------------------------------------------------------

# 5. Collector Architecture

    Exchange Connector

            |

    Data Normalizer

            |

    Event Producer

            |

    Kafka Topic

------------------------------------------------------------------------

# 6. Exchange Connector

Each exchange has an independent connector.

Example:

    collector/

    ├── binance/

    ├── okx/

    └── bybit/

Benefits:

-   Fault isolation
-   Independent upgrade
-   Easy extension

------------------------------------------------------------------------

# 7. WebSocket Collection

Real-time data uses WebSocket.

Flow:

    Connect

    ↓

    Subscribe Channels

    ↓

    Receive Events

    ↓

    Validate

    ↓

    Normalize

    ↓

    Publish

------------------------------------------------------------------------

# 8. REST Data Compensation

REST APIs are used for:

-   Initial synchronization
-   Missing data recovery
-   Historical backfill

Example:

    WebSocket Failure

    ↓

    REST Recovery

    ↓

    Resume Streaming

------------------------------------------------------------------------

# 9. Data Normalization

Different exchanges have different formats.

Collector converts:

Exchange Format

↓

Unified Format

Example:

``` json
{
 "exchange":"binance",
 "symbol":"BTCUSDT",
 "price":68000,
 "timestamp":1700000000000
}
```

------------------------------------------------------------------------

# 10. Kafka Topic Design

Topics:

    market.ticker

    market.trade

    market.kline

    market.funding

    market.open_interest

    market.liquidation

------------------------------------------------------------------------

# 11. Event Format

Standard event:

``` json
{
 "event":"market.trade",
 "exchange":"binance",
 "timestamp":1700000000000,
 "data":{}
}
```

------------------------------------------------------------------------

# 12. Connection Management

Collector handles:

-   Connection monitoring
-   Heartbeat
-   Reconnect
-   Subscription recovery

------------------------------------------------------------------------

# 13. Error Handling

Failures:

-   Network error
-   Exchange timeout
-   Invalid data
-   Rate limit

Strategy:

-   Retry
-   Backoff
-   Logging
-   Alerting

------------------------------------------------------------------------

# 14. Rate Limit Management

Each connector manages:

-   API limits
-   Request frequency
-   Subscription limits

------------------------------------------------------------------------

# 15. Data Validation

Before publishing:

Check:

-   Symbol validity
-   Timestamp
-   Price range
-   Data completeness

------------------------------------------------------------------------

# 16. Storage Strategy

Collector does not directly store analytical data.

Data goes through:

    Collector

    ↓

    Kafka

    ↓

    Storage Services

------------------------------------------------------------------------

# 17. Monitoring

Monitor:

-   Connection status
-   Event latency
-   Event throughput
-   Error rate
-   Kafka publishing status

------------------------------------------------------------------------

# 18. Deployment

Collector services are deployed independently.

Example:

    collector-binance

    collector-okx

    collector-bybit

------------------------------------------------------------------------

# 19. Testing

Required:

-   Connector tests
-   Data normalization tests
-   Reconnection tests
-   Load tests

------------------------------------------------------------------------

# 20. Future Extensions

Reserved:

-   More exchanges
-   On-chain collector
-   Social sentiment collector
-   Alternative data collector

------------------------------------------------------------------------

# 21. Compliance

Every collector must define:

-   Data source
-   Connector implementation
-   Event format
-   Monitoring metrics
-   Failure recovery

This document defines the official Collector Service architecture.
