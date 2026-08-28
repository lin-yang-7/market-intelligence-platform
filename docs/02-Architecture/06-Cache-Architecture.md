# Cache Architecture

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the caching architecture of the Market
Intelligence Platform.

Redis is used as the primary real-time cache layer to provide
low-latency access for APIs, WebSocket services, and real-time
intelligence features.

------------------------------------------------------------------------

# 2. Cache Goals

The cache layer provides:

-   Low latency access
-   Reduced database pressure
-   Real-time data distribution
-   API performance optimization
-   WebSocket acceleration

------------------------------------------------------------------------

# 3. Cache Architecture

    Client

     |

    API Gateway

     |

    Business Services

     |

    Redis Cache

     |

    MySQL / ClickHouse

The application follows a cache-first strategy for high-frequency data.

------------------------------------------------------------------------

# 4. Cache Categories

## Market Cache

Stores real-time market information.

Examples:

    market:ticker:{symbol}

    market:depth:{symbol}

    market:funding:{symbol}

    market:oi:{symbol}

Purpose:

-   Fast market APIs
-   WebSocket updates

------------------------------------------------------------------------

## Ranking Cache

Stores calculated rankings.

Examples:

    ranking:overall

    ranking:long

    ranking:short

    ranking:momentum

Purpose:

-   Dashboard
-   API responses

------------------------------------------------------------------------

## Feature Cache

Stores latest quantitative features.

Examples:

    feature:{symbol}:{name}

Examples:

    feature:BTCUSDT:rsi

    feature:ETHUSDT:volume_ratio

Consumers:

-   Rule Engine
-   Signal Engine
-   Screener

------------------------------------------------------------------------

## Signal Cache

Stores active signals.

Examples:

    signal:latest

    signal:{id}

Used by:

-   Dashboard
-   WebSocket
-   Alert Service

------------------------------------------------------------------------

## User Cache

Stores temporary user data.

Examples:

    session:{id}

    permission:{user_id}

------------------------------------------------------------------------

# 5. Cache Key Standards

Format:

    {domain}:{resource}:{identifier}

Examples:

    market:ticker:BTCUSDT

    feature:rsi:BTCUSDT

    signal:id:12345

Rules:

-   Lowercase
-   Clear naming
-   No random keys
-   Include version when necessary

------------------------------------------------------------------------

# 6. TTL Strategy

## Real-Time Market Data

TTL:

Seconds

Examples:

-   ticker
-   order book

------------------------------------------------------------------------

## Ranking Data

TTL:

Seconds to minutes

Depends on calculation frequency.

------------------------------------------------------------------------

## Feature Data

TTL:

Based on feature update interval.

Examples:

-   1 minute feature
-   5 minute feature

------------------------------------------------------------------------

## Session Data

TTL:

Hours or days.

------------------------------------------------------------------------

# 7. Cache Update Strategy

## Write Through

Used for:

-   Critical real-time values

Flow:

    Event

    ↓

    Service

    ↓

    Redis

    ↓

    Storage

------------------------------------------------------------------------

## Cache Aside

Used for:

-   Historical queries

Flow:

    Request

    ↓

    Redis

    ↓

    Database if missing

------------------------------------------------------------------------

# 8. Cache Consistency

Consistency priority:

Real-time data:

Redis first.

Historical data:

ClickHouse first.

Business data:

MySQL first.

------------------------------------------------------------------------

# 9. Cache Failure Handling

When Redis is unavailable:

System should:

-   Continue service degradation
-   Read from databases when possible
-   Recover cache automatically

------------------------------------------------------------------------

# 10. Preventing Cache Problems

## Cache Breakdown

Solutions:

-   Distributed locks
-   Request throttling

------------------------------------------------------------------------

## Cache Avalanche

Solutions:

-   Randomized TTL
-   Batch refresh

------------------------------------------------------------------------

## Cache Penetration

Solutions:

-   Input validation
-   Empty result caching

------------------------------------------------------------------------

# 11. Redis Deployment

Production:

-   Redis Cluster

or

-   Redis Sentinel

Requirements:

-   High availability
-   Persistence
-   Monitoring

------------------------------------------------------------------------

# 12. Monitoring

Monitor:

-   Memory usage
-   Hit rate
-   Latency
-   Key count
-   Eviction rate
-   Connection count

Metrics exported to Prometheus.

------------------------------------------------------------------------

# 13. Future Extensions

Reserved:

-   Redis Streams
-   Real-time event cache
-   Distributed feature cache
-   Multi-region cache

------------------------------------------------------------------------

# 14. Compliance

All services using Redis must define:

-   Key naming
-   TTL policy
-   Update strategy
-   Failure handling
-   Monitoring metrics

This document defines the official cache architecture.
