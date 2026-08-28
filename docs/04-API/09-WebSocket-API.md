# WebSocket API

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the WebSocket API of the Market Intelligence
Platform.

WebSocket API provides real-time data streaming for applications
requiring low-latency updates.

Core scenarios:

-   Real-time market updates
-   Ranking changes
-   Signal notifications
-   Alert notifications

------------------------------------------------------------------------

# 2. WebSocket Endpoint

Example:

    wss://api.example.com/v1/ws

Protocol:

    WebSocket Secure (WSS)

------------------------------------------------------------------------

# 3. Connection Flow

    Client

    ↓

    WebSocket Connect

    ↓

    Authentication

    ↓

    Subscribe Channel

    ↓

    Receive Events

    ↓

    Heartbeat

------------------------------------------------------------------------

# 4. Authentication

Connection request:

Example:

    ?apiKey=xxxxx

or Header:

    Authorization: Bearer token

Authenticated users can access private channels.

------------------------------------------------------------------------

# 5. Channel Design

Format:

    {domain}.{event}

Examples:

    market.ticker

    ranking.updated

    signal.created

    alert.triggered

------------------------------------------------------------------------

# 6. Market Ticker Channel

Channel:

    market.ticker

Purpose:

Real-time price updates.

------------------------------------------------------------------------

Event Example:

``` json
{
 "event":"market.ticker",
 "data":{
  "symbol":"BTCUSDT",
  "price":68000,
  "timestamp":1700000000000
 }
}
```

------------------------------------------------------------------------

# 7. Ranking Channel

Channel:

    ranking.updated

Purpose:

Push ranking changes.

------------------------------------------------------------------------

Event Example:

``` json
{
 "event":"ranking.updated",
 "data":{
  "type":"longInflow",
  "symbol":"BTCUSDT",
  "rank":1,
  "score":95
 }
}
```

------------------------------------------------------------------------

# 8. Signal Channel

Channel:

    signal.created

Purpose:

Receive new intelligent signals.

------------------------------------------------------------------------

Event Example:

``` json
{
 "event":"signal.created",
 "data":{
  "symbol":"BTCUSDT",
  "type":"longInflow",
  "score":96,
  "confidence":0.94
 }
}
```

------------------------------------------------------------------------

# 9. Alert Channel

Channel:

    alert.triggered

Purpose:

Receive user alert events.

------------------------------------------------------------------------

Event Example:

``` json
{
 "event":"alert.triggered",
 "data":{
  "alertId":"alert_001",
  "symbol":"BTCUSDT",
  "message":"Long inflow detected"
 }
}
```

------------------------------------------------------------------------

# 10. Subscribe Message

Client sends:

``` json
{
 "action":"subscribe",
 "channels":[
  "signal.created",
  "ranking.updated"
 ]
}
```

------------------------------------------------------------------------

# 11. Unsubscribe Message

``` json
{
 "action":"unsubscribe",
 "channels":[
  "ranking.updated"
 ]
}
```

------------------------------------------------------------------------

# 12. Heartbeat

Client:

    ping

Server:

    pong

Recommended interval:

30 seconds

------------------------------------------------------------------------

# 13. Reconnection Strategy

Client should support:

-   Automatic reconnect
-   Exponential backoff
-   Channel resubscription
-   Event recovery

------------------------------------------------------------------------

# 14. Event Standard

All events include:

``` json
{
 "event":"",
 "timestamp":"",
 "data":{}
}
```

------------------------------------------------------------------------

# 15. Connection Limits

Limits depend on:

-   User plan
-   API subscription
-   Connection count

------------------------------------------------------------------------

# 16. Error Events

Example:

``` json
{
 "event":"error",
 "code":1001,
 "message":"Unauthorized"
}
```

------------------------------------------------------------------------

# 17. Performance Requirements

Targets:

-   Low latency delivery
-   Stable connections
-   Event ordering
-   Duplicate handling

------------------------------------------------------------------------

# 18. Future Extensions

Reserved:

-   Private trading channel
-   AI signal stream
-   Strategy execution stream
-   Portfolio stream

------------------------------------------------------------------------

# 19. Compliance

Every WebSocket channel must define:

-   Channel name
-   Event schema
-   Permission requirement
-   Rate limit
-   Recovery mechanism

This document defines the official WebSocket API standard.
