# Alert Service

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the Alert Service architecture of the Market
Intelligence Platform.

Alert Service provides automated notification capabilities based on:

-   Signals
-   Rankings
-   Market conditions
-   User-defined rules

It powers:

-   Long Inflow Alert
-   Signal Alert
-   Price Alert
-   Webhook Notification
-   User Notification

------------------------------------------------------------------------

# 2. Alert Service Role

Data flow:

    Signal Service

    ↓

    Alert Service

    ↓

    Notification Service

    ↓

    User

Alert Service responsibilities:

-   Rule management
-   Condition evaluation
-   Alert triggering
-   Notification delivery
-   Alert history

------------------------------------------------------------------------

# 3. Alert Architecture

    Signal Event

    ↓

    Alert Engine

    ↓

    Rule Evaluation

    ↓

    Notification Queue

    ↓

    Notification Provider

------------------------------------------------------------------------

# 4. Alert Types

Supported:

  Type         Description
  ------------ -------------------------
  longInflow   Capital inflow alert
  signal       Signal generated alert
  price        Price condition alert
  ranking      Ranking change alert
  feature      Feature threshold alert

------------------------------------------------------------------------

# 5. User Alert Rule

Each alert contains:

-   User ID
-   Alert type
-   Conditions
-   Notification channel
-   Status
-   Created time

Example:

``` json
{
 "type":"longInflow",
 "condition":{
  "score":">90"
 },
 "channel":"telegram"
}
```

------------------------------------------------------------------------

# 6. Alert Engine

Responsibilities:

-   Receive events
-   Match rules
-   Trigger alerts
-   Prevent duplicates

Flow:

    Event

    ↓

    Rule Matching

    ↓

    Trigger Decision

    ↓

    Create Alert Record

------------------------------------------------------------------------

# 7. Long Inflow Alert

Purpose:

Notify users when strong capital inflow opportunities appear.

Conditions:

-   Long inflow score
-   Confidence level
-   Volume increase
-   Ranking position

Example:

    IF

    long_inflow_score > 90

    AND

    confidence > 0.9

    THEN

    trigger alert

------------------------------------------------------------------------

# 8. Notification Service

Supported channels:

## Webhook

For:

-   External applications
-   Trading systems

------------------------------------------------------------------------

## Telegram

For:

-   Real-time user notifications

------------------------------------------------------------------------

## Email

For:

-   Account messages

------------------------------------------------------------------------

# 9. Notification Queue

Architecture:

    Alert Event

    ↓

    Kafka

    ↓

    Notification Worker

    ↓

    Provider

Benefits:

-   Async delivery
-   Retry support
-   Failure isolation

------------------------------------------------------------------------

# 10. Retry Strategy

Notification failures support:

-   Automatic retry
-   Exponential backoff
-   Failure logging

------------------------------------------------------------------------

# 11. Duplicate Prevention

The system prevents:

-   Repeated alerts
-   Event duplication
-   Notification spam

Methods:

-   Event ID
-   Cooldown period
-   Alert state tracking

------------------------------------------------------------------------

# 12. Alert Storage

MySQL:

Stores:

-   User rules
-   Alert configuration
-   Alert status

ClickHouse:

Stores:

-   Historical alert events

Redis:

Stores:

-   Active alert cache

------------------------------------------------------------------------

# 13. Alert Event

Example:

``` json
{
 "event":"alert.triggered",
 "timestamp":1700000000000,
 "data":{
  "symbol":"BTCUSDT",
  "type":"longInflow"
 }
}
```

------------------------------------------------------------------------

# 14. API Integration

Provides:

    POST /v1/alert/create

    GET /v1/alert/list

    GET /v1/alert/history

------------------------------------------------------------------------

# 15. Monitoring

Monitor:

-   Trigger latency
-   Notification success rate
-   Queue backlog
-   Provider status

------------------------------------------------------------------------

# 16. Testing

Required:

-   Rule tests
-   Notification tests
-   Retry tests
-   Load tests

------------------------------------------------------------------------

# 17. Future Extensions

Reserved:

-   AI generated alerts
-   Trading automation
-   Portfolio alerts
-   Multi-channel intelligent routing

------------------------------------------------------------------------

# 18. Compliance

Every alert model must define:

-   Trigger rules
-   Notification method
-   Frequency limit
-   Storage strategy
-   Version

This document defines the official Alert Service architecture.
