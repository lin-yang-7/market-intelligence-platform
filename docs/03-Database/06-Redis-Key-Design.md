# Redis Key Design

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the Redis key design and cache management strategy
for the Market Intelligence Platform.

Redis is used for real-time data access, high-frequency queries, session
management, and temporary state storage.

------------------------------------------------------------------------

# 2. Redis Design Principles

All Redis usage follows:

-   Clear key naming
-   Predictable structure
-   Controlled TTL
-   Avoid unnecessary persistence
-   Monitoring enabled
-   Cache failure tolerance

------------------------------------------------------------------------

# 3. Key Naming Convention

Format:

    {domain}:{resource}:{identifier}

Examples:

    market:ticker:BTCUSDT

    ranking:long

    feature:BTCUSDT:rsi

Rules:

-   Lowercase
-   Use colon separator
-   Include business meaning
-   Avoid random keys

------------------------------------------------------------------------

# 4. Market Cache

## Ticker Cache

Key:

    market:ticker:{symbol}

Example:

    market:ticker:BTCUSDT

Stores:

-   Price
-   Bid
-   Ask
-   Volume
-   Change rate
-   Timestamp

TTL:

Seconds

------------------------------------------------------------------------

## Order Book Cache

Key:

    market:depth:{symbol}

Stores:

-   Bid levels
-   Ask levels
-   Update timestamp

TTL:

Seconds

------------------------------------------------------------------------

## Funding Cache

Key:

    market:funding:{symbol}

Stores:

-   Funding rate
-   Next funding time

TTL:

Minutes

------------------------------------------------------------------------

# 5. Ranking Cache

## Ranking Result

Keys:

    ranking:overall

    ranking:long

    ranking:short

    ranking:momentum

Stores:

-   Symbol list
-   Score
-   Ranking position
-   Update time

TTL:

Seconds to minutes

------------------------------------------------------------------------

# 6. Feature Cache

## Latest Feature

Key:

    feature:{symbol}:{feature_name}

Examples:

    feature:BTCUSDT:rsi

    feature:BTCUSDT:volume_ratio

Stores:

-   Feature value
-   Version
-   Timestamp

TTL:

Based on calculation interval

------------------------------------------------------------------------

# 7. Signal Cache

## Latest Signals

Key:

    signal:latest

Stores:

-   Recent signals
-   Signal score
-   Confidence

------------------------------------------------------------------------

## Signal Detail

Key:

    signal:{signal_id}

Stores:

-   Symbol
-   Type
-   Reason
-   Timestamp

------------------------------------------------------------------------

# 8. Session Cache

## User Session

Key:

    session:{session_id}

Stores:

-   User ID
-   Login status
-   Expiration

TTL:

Hours

------------------------------------------------------------------------

## Permission Cache

Key:

    permission:{user_id}

Stores:

-   Roles
-   Permissions

TTL:

Minutes

------------------------------------------------------------------------

# 9. WebSocket Cache

## Connection State

Key:

    ws:connection:{id}

Stores:

-   User
-   Channels
-   Status

------------------------------------------------------------------------

## Subscription State

Key:

    ws:subscription:{id}

Stores:

-   Active subscriptions
-   Topics

------------------------------------------------------------------------

# 10. Cache Update Strategy

## Event Driven Update

Flow:

    Kafka Event

    ↓

    Service

    ↓

    Redis Update

Example:

    market.ticker

    ↓

    market-service

    ↓

    market:ticker:BTCUSDT

------------------------------------------------------------------------

# 11. Cache Expiration Strategy

Different data uses different TTL.

Examples:

  Data            TTL
  --------------- -------------------
  Price           Seconds
  Ranking         Minutes
  Feature         Calculation Cycle
  Session         Hours
  Configuration   Long

------------------------------------------------------------------------

# 12. Cache Failure Strategy

When Redis fails:

-   APIs fallback when possible
-   Database queries used
-   Cache rebuilt automatically

------------------------------------------------------------------------

# 13. Cache Monitoring

Monitor:

-   Hit rate
-   Memory usage
-   Key count
-   Eviction
-   Latency
-   Connection status

------------------------------------------------------------------------

# 14. Security

Requirements:

-   Authentication enabled
-   Network isolation
-   Access control
-   No sensitive data without protection

------------------------------------------------------------------------

# 15. Future Extensions

Reserved:

-   Redis Streams
-   Distributed cache
-   Real-time feature cache
-   Multi-region cache

------------------------------------------------------------------------

# 16. Compliance

Every Redis key must define:

-   Owner service
-   Purpose
-   TTL
-   Update method
-   Failure strategy

This document defines the official Redis key architecture.
