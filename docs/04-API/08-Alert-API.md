# Alert API

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the Alert API of the Market Intelligence Platform.

Alert API provides automated notification capabilities based on market
conditions, signals, rankings, and user-defined rules.

Core scenarios:

-   Long Inflow Alert
-   Signal Alert
-   Price Alert
-   Feature Alert
-   Webhook Notification

------------------------------------------------------------------------

# 2. API Base Path

    /v1/alert

------------------------------------------------------------------------

# 3. Alert Concept

An alert contains:

-   Trigger condition
-   Monitoring object
-   Notification channel
-   Trigger history

Flow:

    Market Data

    ↓

    Feature / Signal Engine

    ↓

    Alert Engine

    ↓

    Notification Service

    ↓

    User

------------------------------------------------------------------------

# 4. Alert Types

Supported:

  Type         Description
  ------------ --------------------------
  longInflow   Long inflow signal alert
  price        Price condition alert
  feature      Feature value alert
  ranking      Ranking change alert
  signal       Signal generated alert

------------------------------------------------------------------------

# 5. Create Alert API

## Endpoint

    POST /alert/create

Purpose:

Create a user alert rule.

------------------------------------------------------------------------

## Request

``` json
{
 "type":"longInflow",
 "symbol":"BTCUSDT",
 "conditions":{
   "score":">90"
 },
 "channel":"webhook"
}
```

------------------------------------------------------------------------

## Response

``` json
{
 "code":0,
 "data":{
  "alertId":"alert_001",
  "status":"active"
 }
}
```

------------------------------------------------------------------------

# 6. Alert List API

## Endpoint

    GET /alert/list

Purpose:

Get user alert rules.

------------------------------------------------------------------------

## Response

``` json
{
 "data":[
  {
   "alertId":"alert_001",
   "type":"longInflow",
   "enabled":true
  }
 ]
}
```

------------------------------------------------------------------------

# 7. Update Alert API

## Endpoint

    POST /alert/update

Purpose:

Modify alert configuration.

------------------------------------------------------------------------

Parameters:

-   alertId
-   conditions
-   channel
-   enabled

------------------------------------------------------------------------

# 8. Delete Alert API

## Endpoint

    DELETE /alert/{alertId}

Purpose:

Remove alert rule.

------------------------------------------------------------------------

# 9. Long Inflow Alert API

## Endpoint

    POST /alert/longInflow

Purpose:

Create intelligent long inflow monitoring.

------------------------------------------------------------------------

## Conditions

Supported:

-   Score threshold
-   Inflow amount
-   Volume increase
-   Confidence level

Example:

``` json
{
 "score":">90",
 "confidence":">0.9",
 "timeframe":"1h"
}
```

------------------------------------------------------------------------

# 10. Signal Alert API

## Endpoint

    POST /alert/signal

Purpose:

Create signal-based alert.

Example:

``` json
{
 "signalType":"breakout",
 "minScore":85
}
```

------------------------------------------------------------------------

# 11. Notification Channels

Supported:

## Webhook

For:

-   Trading systems
-   External applications

------------------------------------------------------------------------

## Telegram

For:

-   Personal notifications

------------------------------------------------------------------------

## Email

For:

-   Account notifications

------------------------------------------------------------------------

# 12. Alert History API

## Endpoint

    GET /alert/history

Purpose:

Query triggered alerts.

------------------------------------------------------------------------

Response:

``` json
{
 "data":[
  {
   "alertId":"alert_001",
   "symbol":"BTCUSDT",
   "triggerTime":1700000000000,
   "result":"success"
  }
 ]
}
```

------------------------------------------------------------------------

# 13. Alert Status

States:

    active

    paused

    triggered

    disabled

------------------------------------------------------------------------

# 14. Alert Limits

Limits depend on:

-   Subscription plan
-   Number of rules
-   Notification frequency

------------------------------------------------------------------------

# 15. Security

Alert APIs require:

-   Authentication
-   Permission validation
-   User ownership verification

------------------------------------------------------------------------

# 16. Error Codes

  Code   Meaning
  ------ ---------------------
  7001   Alert not found
  7002   Invalid condition
  7003   Notification failed

------------------------------------------------------------------------

# 17. Future Extensions

Reserved:

-   AI generated alerts
-   Strategy alerts
-   Portfolio alerts
-   Multi-channel automation

------------------------------------------------------------------------

# 18. Compliance

Every Alert API must define:

-   Trigger condition
-   Notification method
-   Frequency limit
-   Permission scope
-   History storage

This document defines the official Alert API standard.
