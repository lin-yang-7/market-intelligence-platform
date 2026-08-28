# Score Service

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the Score Service architecture of the Market
Intelligence Platform.

Score Service converts quantitative features into standardized scores
used by:

-   Ranking Engine
-   Screener Engine
-   Signal Engine
-   AI analysis

------------------------------------------------------------------------

# 2. Score Service Role

Data flow:

    Feature Service

    ↓

    Score Service

    ↓

    Ranking Service

    ↓

    Signal Service

Score Service is responsible for:

-   Feature aggregation
-   Weight calculation
-   Score generation
-   Score explanation

------------------------------------------------------------------------

# 3. Scoring Architecture

    Feature Input

    ↓

    Score Calculator

    ↓

    Weight Engine

    ↓

    Score Result

    ↓

    Score Storage

------------------------------------------------------------------------

# 4. Score Types

Supported scores:

  Score               Description
  ------------------- -------------------------
  Long Inflow Score   Capital inflow strength
  Momentum Score      Trend strength
  Volume Score        Market activity
  Risk Score          Risk evaluation
  Overall Score       Comprehensive score

------------------------------------------------------------------------

# 5. Score Calculation Model

Basic model:

    Final Score

    =

    Feature Value

    ×

    Weight

    +

    Adjustment Factor

Example:

    Long Inflow Score

    =

    Capital Flow * 40%

    +

    Volume Strength * 30%

    +

    Price Confirmation * 20%

    +

    Market Condition * 10%

------------------------------------------------------------------------

# 6. Long Inflow Score

Purpose:

Identify assets with strong buying pressure.

Factors:

-   Net inflow
-   Large order ratio
-   Volume acceleration
-   Price confirmation
-   Open interest change

Output:

``` json
{
 "symbol":"BTCUSDT",
 "score":95,
 "type":"longInflow"
}
```

------------------------------------------------------------------------

# 7. Momentum Score

Factors:

-   Price trend
-   Moving average
-   Breakout strength
-   Historical performance

------------------------------------------------------------------------

# 8. Volume Score

Factors:

-   Volume increase
-   Trading activity
-   Market participation

------------------------------------------------------------------------

# 9. Risk Score

Factors:

-   Volatility
-   Liquidity
-   Drawdown
-   Market risk

------------------------------------------------------------------------

# 10. Weight Management

Weights are configurable.

Example:

``` json
{
 "capital_flow":0.4,
 "volume":0.3,
 "momentum":0.2,
 "risk":0.1
}
```

------------------------------------------------------------------------

# 11. Score Version

Every scoring model requires versioning.

Example:

    long_inflow:v1

    long_inflow:v2

Version changes require:

-   Historical comparison
-   Performance evaluation
-   Migration plan

------------------------------------------------------------------------

# 12. Real-time Score Pipeline

    Feature Updated Event

    ↓

    Score Service

    ↓

    Calculate Score

    ↓

    Redis Cache

    ↓

    Ranking API

------------------------------------------------------------------------

# 13. Historical Score Pipeline

    Historical Features

    ↓

    Batch Calculation

    ↓

    ClickHouse

    ↓

    Backtesting

------------------------------------------------------------------------

# 14. Score Explanation

Every score should provide:

-   Score value
-   Factor contribution
-   Calculation version
-   Timestamp

Example:

``` json
{
 "score":92,
 "factors":{
  "inflow":95,
  "volume":88
 }
}
```

------------------------------------------------------------------------

# 15. Score Storage

Redis:

-   Latest score

ClickHouse:

-   Historical score

------------------------------------------------------------------------

# 16. Quality Control

Validate:

-   Feature availability
-   Weight correctness
-   Score range
-   Calculation consistency

Score range:

    0 - 100

------------------------------------------------------------------------

# 17. Monitoring

Monitor:

-   Calculation latency
-   Score distribution
-   Model changes
-   Processing errors

------------------------------------------------------------------------

# 18. Testing

Required:

-   Formula tests
-   Historical validation
-   Regression tests
-   Performance tests

------------------------------------------------------------------------

# 19. Future Extensions

Reserved:

-   Machine learning scoring
-   Adaptive weights
-   Reinforcement learning model
-   AI ranking optimization

------------------------------------------------------------------------

# 20. Compliance

Every scoring model must define:

-   Formula
-   Features
-   Weights
-   Version
-   Validation result

This document defines the official Score Service architecture.
