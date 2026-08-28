# Ranking Service

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the Ranking Service architecture of the Market
Intelligence Platform.

Ranking Service converts scores and features into ordered market
rankings.

It powers:

-   Intelligent coin selection
-   Long Inflow ranking
-   Market opportunity discovery
-   Screener results
-   Ranking API

------------------------------------------------------------------------

# 2. Ranking Service Role

Data flow:

    Feature Service

    ↓

    Score Service

    ↓

    Ranking Service

    ↓

    API / WebSocket / Screener

Ranking Service focuses on:

-   Sorting
-   Ranking generation
-   Ranking updates
-   Ranking distribution

------------------------------------------------------------------------

# 3. Ranking Architecture

    Score Events

    ↓

    Ranking Calculator

    ↓

    Ranking Cache

    ↓

    Ranking API

------------------------------------------------------------------------

# 4. Ranking Types

Supported rankings:

  Type         Description
  ------------ ------------------------------
  overall      Comprehensive market ranking
  longInflow   Long capital inflow ranking
  momentum     Momentum strength ranking
  volume       Volume activity ranking
  volatility   Market volatility ranking

------------------------------------------------------------------------

# 5. Ranking Calculation

Basic flow:

    Score Input

    ↓

    Filter Rules

    ↓

    Sort

    ↓

    Generate Top N

    ↓

    Publish Result

------------------------------------------------------------------------

# 6. Long Inflow Ranking

Purpose:

Identify assets with strong capital inflow.

Input:

-   Long Inflow Score
-   Volume Score
-   Momentum Score
-   Market conditions

Output:

``` json
{
 "rank":1,
 "symbol":"BTCUSDT",
 "score":95,
 "type":"longInflow"
}
```

------------------------------------------------------------------------

# 7. Overall Ranking

Combines:

-   Trend
-   Volume
-   Capital flow
-   Risk

Example:

    Overall Score

    =

    Long Score

    +

    Momentum Score

    +

    Risk Adjustment

------------------------------------------------------------------------

# 8. Ranking Filters

Supported filters:

-   Exchange
-   Symbol
-   Market type
-   Minimum score
-   Time range

------------------------------------------------------------------------

# 9. Top N Generation

Examples:

    Top 10

    Top 50

    Top 100

Generated rankings are cached for fast access.

------------------------------------------------------------------------

# 10. Real-time Ranking Pipeline

    Score Updated Event

    ↓

    Ranking Service

    ↓

    Calculate Ranking

    ↓

    Redis Update

    ↓

    WebSocket Push

------------------------------------------------------------------------

# 11. Ranking Cache

Redis keys:

    ranking:overall

    ranking:longInflow

    ranking:momentum

Stored:

-   Symbol
-   Rank
-   Score
-   Timestamp

------------------------------------------------------------------------

# 12. Historical Ranking

Historical rankings stored in:

ClickHouse

Used for:

-   Analysis
-   Backtesting
-   Model evaluation

------------------------------------------------------------------------

# 13. Ranking API Integration

Provides data for:

    GET /v1/ranking/longInflow

Response:

``` json
{
 "symbol":"BTCUSDT",
 "rank":1,
 "score":95
}
```

------------------------------------------------------------------------

# 14. Ranking Event

Event example:

``` json
{
 "event":"ranking.updated",
 "type":"longInflow",
 "timestamp":1700000000000
}
```

------------------------------------------------------------------------

# 15. Performance Requirements

Optimization:

-   Redis ranking cache
-   Incremental update
-   Parallel calculation
-   Batch processing

------------------------------------------------------------------------

# 16. Monitoring

Monitor:

-   Ranking calculation latency
-   Update frequency
-   Cache hit rate
-   Result consistency

------------------------------------------------------------------------

# 17. Testing

Required:

-   Ranking logic tests
-   Performance tests
-   Historical comparison
-   Regression tests

------------------------------------------------------------------------

# 18. Future Extensions

Reserved:

-   Personalized ranking
-   AI ranking model
-   Strategy ranking
-   Portfolio ranking

------------------------------------------------------------------------

# 19. Compliance

Every ranking model must define:

-   Ranking formula
-   Input data
-   Score dependency
-   Update frequency
-   Version

This document defines the official Ranking Service architecture.
