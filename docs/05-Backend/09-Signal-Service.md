# Signal Service

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the Signal Service architecture of the Market
Intelligence Platform.

Signal Service converts rankings, scores, and market conditions into
actionable intelligence signals.

It powers:

-   Long Inflow Alert
-   Signal API
-   Alert Engine
-   WebSocket signal stream

------------------------------------------------------------------------

# 2. Signal Service Role

Data flow:

    Feature Service

    ↓

    Score Service

    ↓

    Ranking Service

    ↓

    Signal Service

    ↓

    Alert Service / API

Signal Service is responsible for:

-   Signal generation
-   Signal validation
-   Signal lifecycle management
-   Signal explanation

------------------------------------------------------------------------

# 3. Signal Architecture

    Ranking Event

    ↓

    Signal Engine

    ↓

    Signal Rules

    ↓

    Signal Storage

    ↓

    Notification Layer

------------------------------------------------------------------------

# 4. Signal Types

Supported:

  Type         Description
  ------------ -----------------------
  longInflow   Strong capital inflow
  breakout     Price breakout
  momentum     Trend acceleration
  reversal     Trend reversal
  volatility   Abnormal volatility

------------------------------------------------------------------------

# 5. Signal Generation Flow

    Ranking Update

    ↓

    Condition Evaluation

    ↓

    Signal Score

    ↓

    Confidence Calculation

    ↓

    Create Signal

------------------------------------------------------------------------

# 6. Long Inflow Signal

Purpose:

Detect assets with significant buying pressure.

Input factors:

-   Long inflow score
-   Volume strength
-   Price confirmation
-   Open interest change
-   Market condition

Example:

``` json
{
 "symbol":"BTCUSDT",
 "type":"longInflow",
 "score":96,
 "confidence":0.94
}
```

------------------------------------------------------------------------

# 7. Signal Rule Engine

Rules define when signals are triggered.

Example:

    IF

    long_inflow_score > 90

    AND

    volume_ratio > 2

    THEN

    create longInflow signal

------------------------------------------------------------------------

# 8. Signal Confidence

Confidence represents signal reliability.

Factors:

-   Data quality
-   Feature agreement
-   Historical performance
-   Market environment

Range:

    0 - 1

------------------------------------------------------------------------

# 9. Signal Lifecycle

States:

    created

    ↓

    active

    ↓

    expired

    ↓

    archived

------------------------------------------------------------------------

# 10. Signal Storage

Redis:

Latest active signals

Example:

    signal:latest

------------------------------------------------------------------------

ClickHouse:

Historical signals

Used for:

-   Analysis
-   Backtesting
-   Model evaluation

------------------------------------------------------------------------

# 11. Signal Event

Event format:

``` json
{
 "event":"signal.created",
 "timestamp":1700000000000,
 "data":{
  "symbol":"BTCUSDT",
  "type":"longInflow"
 }
}
```

------------------------------------------------------------------------

# 12. Signal API Integration

Provides:

    GET /v1/signal/current

    GET /v1/signal/history

    GET /v1/signal/detail

------------------------------------------------------------------------

# 13. WebSocket Integration

Real-time channel:

    signal.created

Pushes:

-   New signal
-   Score change
-   Signal expiration

------------------------------------------------------------------------

# 14. Signal Explanation

Each signal contains:

-   Trigger reason
-   Factor contribution
-   Confidence
-   Model version

Example:

``` json
{
 "reasons":[
  "high_inflow",
  "volume_breakout"
 ]
}
```

------------------------------------------------------------------------

# 15. Signal Quality Control

Validation:

-   Duplicate detection
-   False signal analysis
-   Score consistency
-   Data completeness

------------------------------------------------------------------------

# 16. Monitoring

Monitor:

-   Signal generation latency
-   Signal count
-   Accuracy metrics
-   Processing errors

------------------------------------------------------------------------

# 17. Testing

Required:

-   Rule tests
-   Historical replay tests
-   Performance tests
-   Regression tests

------------------------------------------------------------------------

# 18. Future Extensions

Reserved:

-   AI signal generation
-   Adaptive signal rules
-   Personalized signals
-   Strategy signals

------------------------------------------------------------------------

# 19. Compliance

Every signal model must define:

-   Rule logic
-   Input features
-   Score dependency
-   Confidence calculation
-   Version

This document defines the official Signal Service architecture.
