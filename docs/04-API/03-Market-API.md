# Market API

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the Market API of the Market Intelligence
Platform.

The Market API provides external access to real-time and historical
market data.

Supported data:

-   Ticker
-   Kline
-   Trade
-   Funding Rate
-   Open Interest
-   Liquidation

------------------------------------------------------------------------

# 2. API Base URL

Example:

    https://api.example.com/v1

All requests use:

    HTTPS

------------------------------------------------------------------------

# 3. Common Parameters

## symbol

Trading pair.

Example:

    BTCUSDT

------------------------------------------------------------------------

## exchange

Exchange name.

Examples:

    binance

    bybit

    okx

------------------------------------------------------------------------

## interval

Kline interval.

Examples:

    1m

    5m

    1h

    4h

    1d

------------------------------------------------------------------------

## startTime

Start timestamp.

Format:

Unix milliseconds.

------------------------------------------------------------------------

## endTime

End timestamp.

------------------------------------------------------------------------

## limit

Maximum records.

Default:

100

Maximum:

1000

------------------------------------------------------------------------

# 4. Ticker API

## Endpoint

    GET /market/ticker

Purpose:

Get latest market snapshot.

------------------------------------------------------------------------

## Request

Parameters:

  Parameter   Required
  ----------- ----------
  symbol      No
  exchange    No

------------------------------------------------------------------------

## Response

``` json
{
  "code":0,
  "data":{
    "symbol":"BTCUSDT",
    "price":68000,
    "change24h":2.5,
    "volume24h":120000000
  }
}
```

------------------------------------------------------------------------

# 5. Kline API

## Endpoint

    GET /market/kline

Purpose:

Get historical candle data.

------------------------------------------------------------------------

## Request

Parameters:

  Parameter   Required
  ----------- ----------
  symbol      Yes
  interval    Yes
  startTime   No
  endTime     No
  limit       No

------------------------------------------------------------------------

## Response

``` json
{
 "code":0,
 "data":[
  {
   "timestamp":1700000000000,
   "open":67000,
   "high":68000,
   "low":66500,
   "close":67500,
   "volume":10000
  }
 ]
}
```

------------------------------------------------------------------------

# 6. Trade API

## Endpoint

    GET /market/trades

Purpose:

Get recent transactions.

------------------------------------------------------------------------

## Response

``` json
{
 "code":0,
 "data":[
  {
   "price":68000,
   "quantity":1.2,
   "side":"buy",
   "timestamp":1700000000000
  }
 ]
}
```

------------------------------------------------------------------------

# 7. Funding API

## Endpoint

    GET /market/funding

Purpose:

Get perpetual contract funding data.

------------------------------------------------------------------------

Response:

``` json
{
 "symbol":"BTCUSDT",
 "fundingRate":0.01,
 "nextFundingTime":1700000000000
}
```

------------------------------------------------------------------------

# 8. Open Interest API

## Endpoint

    GET /market/openInterest

Purpose:

Get futures open interest.

------------------------------------------------------------------------

Response:

``` json
{
 "symbol":"BTCUSDT",
 "openInterest":1000000000,
 "changeRate":5.2
}
```

------------------------------------------------------------------------

# 9. Liquidation API

## Endpoint

    GET /market/liquidation

Purpose:

Get liquidation events.

------------------------------------------------------------------------

Response:

``` json
{
 "symbol":"BTCUSDT",
 "side":"long",
 "value":500000,
 "timestamp":1700000000000
}
```

------------------------------------------------------------------------

# 10. Pagination

Large responses support:

Request:

    limit
    cursor

Response:

``` json
{
 "data":[],
 "nextCursor":"xxxx"
}
```

------------------------------------------------------------------------

# 11. Data Accuracy

All market data includes:

-   exchange
-   symbol
-   timestamp
-   source

------------------------------------------------------------------------

# 12. Rate Limits

Limits depend on:

-   API plan
-   Endpoint type
-   API Key

------------------------------------------------------------------------

# 13. Error Codes

  Code   Meaning
  ------ --------------------
  2001   Invalid symbol
  2002   Invalid exchange
  2003   Invalid time range
  5000   Service error

------------------------------------------------------------------------

# 14. Future Extensions

Reserved:

-   Order book API
-   Index price API
-   Basis API
-   ETF data API

------------------------------------------------------------------------

# 15. Compliance

Every Market API endpoint must define:

-   Request schema
-   Response schema
-   Rate limit
-   Authentication
-   Error codes

This document defines the official Market API standard.
