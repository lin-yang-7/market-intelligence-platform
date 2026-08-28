# Screener API

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the Screener API of the Market Intelligence
Platform.

Screener API provides intelligent coin filtering capabilities based on
market conditions, quantitative features, scoring models, and
user-defined rules.

Core scenarios:

-   Intelligent coin selection
-   Strategy screening
-   Multi-factor filtering
-   Custom conditions

------------------------------------------------------------------------

# 2. API Base Path

    /v1/screener

------------------------------------------------------------------------

# 3. Screener Concept

A screener combines:

-   Market conditions
-   Feature values
-   Ranking scores
-   Signal conditions

Flow:

    User Conditions

    ↓

    Screener Engine

    ↓

    Feature Store

    ↓

    Market Data

    ↓

    Result

------------------------------------------------------------------------

# 4. Screener Types

Supported:

  Type         Description
  ------------ ---------------------------
  longInflow   Long inflow screening
  momentum     Momentum screening
  volume       Volume activity screening
  volatility   Volatility screening
  custom       User custom rules

------------------------------------------------------------------------

# 5. Preset Screener List API

## Endpoint

    GET /screener/list

Purpose:

Get available screening strategies.

------------------------------------------------------------------------

## Response

``` json
{
 "code":0,
 "data":[
  {
   "id":"long_inflow_v1",
   "name":"Long Inflow Alert",
   "type":"longInflow"
  }
 ]
}
```

------------------------------------------------------------------------

# 6. Execute Screener API

## Endpoint

    POST /screener/query

Purpose:

Execute coin screening.

------------------------------------------------------------------------

## Request

``` json
{
 "type":"longInflow",
 "timeframe":"1h",
 "limit":50
}
```

------------------------------------------------------------------------

## Response

``` json
{
 "code":0,
 "data":[
  {
   "symbol":"BTCUSDT",
   "score":95,
   "signals":[
    "high_inflow",
    "volume_breakout"
   ]
  }
 ]
}
```

------------------------------------------------------------------------

# 7. Long Inflow Screener

## Endpoint

    POST /screener/longInflow

Purpose:

Find coins with strong capital inflow.

------------------------------------------------------------------------

## Parameters

  Parameter   Description
  ----------- -----------------
  timeframe   Analysis period
  minScore    Minimum score
  minVolume   Minimum volume
  exchange    Exchange filter

------------------------------------------------------------------------

## Response Fields

  Field        Description
  ------------ ----------------
  symbol       Trading pair
  score        Score
  inflow       Capital inflow
  confidence   Confidence
  reasons      Explanation

------------------------------------------------------------------------

# 8. Custom Screener

## Endpoint

    POST /screener/custom

Purpose:

Create custom screening conditions.

------------------------------------------------------------------------

## Request Example

``` json
{
 "conditions":[
  {
   "feature":"volume_ratio",
   "operator":">",
   "value":2
  },
  {
   "feature":"rsi",
   "operator":"<",
   "value":70
  }
 ]
}
```

------------------------------------------------------------------------

# 9. Condition Operators

Supported:

    >

    <

    >=

    <=

    =

    between

    in

------------------------------------------------------------------------

# 10. Saved Screener API

## Create

    POST /screener/save

------------------------------------------------------------------------

## List

    GET /screener/saved

------------------------------------------------------------------------

## Delete

    DELETE /screener/{id}

------------------------------------------------------------------------

# 11. Screener Result Fields

Common fields:

  Field       Description
  ----------- ------------------
  symbol      Trading pair
  score       Composite score
  rank        Ranking position
  signals     Trigger reasons
  timestamp   Update time

------------------------------------------------------------------------

# 12. Data Sources

Screener uses:

-   Market Data API
-   Feature API
-   Ranking Engine
-   Signal Engine

------------------------------------------------------------------------

# 13. Performance Requirements

Optimization:

-   Redis cache
-   Pre-calculated features
-   Async execution

------------------------------------------------------------------------

# 14. Rate Limits

Limits depend on:

-   User plan
-   Screener complexity
-   Execution frequency

------------------------------------------------------------------------

# 15. Error Codes

  Code   Meaning
  ------ ----------------------
  5001   Invalid condition
  5002   Screener unavailable
  5003   No matching coins

------------------------------------------------------------------------

# 16. Future Extensions

Reserved:

-   AI natural language screener
-   Strategy marketplace
-   Backtest integration
-   Personalized screening

------------------------------------------------------------------------

# 17. Compliance

Every Screener API must define:

-   Conditions
-   Data source
-   Calculation logic
-   Response format
-   Permission scope

This document defines the official Screener API standard.
