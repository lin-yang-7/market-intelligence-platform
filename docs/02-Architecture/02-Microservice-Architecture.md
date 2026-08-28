# Microservice Architecture

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the microservice decomposition of the Market
Intelligence Platform.

Each service has clear ownership of business capability, data
responsibility, API boundaries, and deployment lifecycle.

------------------------------------------------------------------------

# 2. Design Principles

All services follow:

-   Single Responsibility
-   Independent Deployment
-   Database Ownership
-   API First
-   Event Driven
-   Horizontal Scaling
-   Observable by Default

No service can directly access another service's database.

------------------------------------------------------------------------

# 3. Service Overview

  Service                 Responsibility
  ----------------------- --------------------------
  gateway-service         API Gateway and routing
  auth-service            Authentication
  user-service            Users and subscriptions
  collector-service       Exchange data collection
  market-service          Real-time market APIs
  history-service         Historical queries
  feature-service         Feature calculation
  feature-store-service   Feature management
  rule-service            Rule evaluation
  score-service           Score calculation
  ranking-service         Ranking service
  screener-service        Intelligent screening
  signal-service          Signal generation
  alert-service           Alert rules
  websocket-service       Real-time streaming
  notification-service    Notifications
  admin-service           Administration
  monitor-service         Monitoring

------------------------------------------------------------------------

# 4. Core Services

## gateway-service

Responsibilities:

-   Request routing
-   Authentication validation
-   Rate limiting
-   API version management

Storage:

None

------------------------------------------------------------------------

## auth-service

Responsibilities:

-   Login
-   Token generation
-   Session management
-   Permission verification

Storage:

MySQL

Cache:

Redis

------------------------------------------------------------------------

## user-service

Responsibilities:

-   User profile
-   API keys
-   Subscription plans
-   Usage quota

Storage:

MySQL

Events:

-   user.created
-   api_key.created
-   subscription.changed

------------------------------------------------------------------------

## collector-service

Responsibilities:

-   Exchange connections
-   WebSocket collection
-   Data normalization

Sources:

-   Binance
-   Bybit
-   OKX

Kafka Topics:

-   market.ticker
-   market.trade
-   market.kline
-   market.depth
-   market.funding
-   market.open_interest

------------------------------------------------------------------------

## market-service

Responsibilities:

Provide:

-   Current price
-   Market snapshot
-   Asset information

Storage:

Redis

Fallback:

ClickHouse

------------------------------------------------------------------------

## history-service

Responsibilities:

Historical queries.

Storage:

ClickHouse

Provides:

-   Klines
-   Trades
-   Funding
-   Features
-   Signals

------------------------------------------------------------------------

## feature-service

Responsibilities:

-   Indicator calculation
-   Feature generation
-   Feature validation

Input:

Market Events

Output:

Feature Events

------------------------------------------------------------------------

## feature-store-service

Responsibilities:

-   Feature catalog
-   Feature registry
-   Feature versioning
-   Feature metadata

Storage:

Redis + ClickHouse + MySQL

------------------------------------------------------------------------

## rule-service

Responsibilities:

-   Rule execution
-   Condition evaluation
-   Strategy logic

Input:

Feature Events

Output:

Score Events

------------------------------------------------------------------------

## score-service

Responsibilities:

-   Composite scoring
-   Score normalization
-   Score history

------------------------------------------------------------------------

## ranking-service

Responsibilities:

Generate:

-   Overall ranking
-   Long ranking
-   Short ranking
-   Momentum ranking

Cache:

Redis

------------------------------------------------------------------------

## screener-service

Responsibilities:

-   Condition filtering
-   Saved screeners
-   Screening execution

APIs:

-   Query Screener
-   Save Screener
-   Manage Screener

------------------------------------------------------------------------

## signal-service

Responsibilities:

-   Signal generation
-   Signal lifecycle
-   Signal explanation

Events:

-   signal.created
-   signal.updated

------------------------------------------------------------------------

## alert-service

Responsibilities:

-   User alert rules
-   Trigger detection
-   Alert state management

------------------------------------------------------------------------

## websocket-service

Responsibilities:

-   Connection management
-   Channel subscription
-   Event broadcasting

Consumes:

Kafka

Provides:

WebSocket

------------------------------------------------------------------------

## notification-service

Responsibilities:

-   Email
-   Telegram
-   Webhook
-   Retry processing

------------------------------------------------------------------------

## admin-service

Responsibilities:

-   User management
-   Configuration
-   Rule management
-   Audit review

------------------------------------------------------------------------

## monitor-service

Responsibilities:

-   Metrics collection
-   Health monitoring
-   Alert integration

------------------------------------------------------------------------

# 5. Service Communication

## Synchronous

Used for:

-   Authentication
-   User operations
-   Configuration

Protocol:

REST API

------------------------------------------------------------------------

## Asynchronous

Used for:

-   Market events
-   Features
-   Signals
-   Notifications

Protocol:

Kafka

------------------------------------------------------------------------

# 6. Data Ownership

## MySQL

Owned by:

-   auth-service
-   user-service
-   admin-service

Contains:

-   Users
-   Permissions
-   API Keys
-   Subscriptions

------------------------------------------------------------------------

## Redis

Owned by:

-   market-service
-   ranking-service
-   websocket-service

Contains:

-   Latest data
-   Cache
-   Sessions

------------------------------------------------------------------------

## ClickHouse

Owned by:

-   history-service
-   feature-store-service

Contains:

-   Historical analytics

------------------------------------------------------------------------

# 7. Scaling Strategy

collector-service:

Scale by exchange.

feature-service:

Scale by Kafka partitions.

ranking-service:

Scale by calculation workload.

websocket-service:

Scale by active connections.

API services:

Scale by traffic.

------------------------------------------------------------------------

# 8. Future Services

Reserved:

-   ai-service
-   backtest-service
-   strategy-service
-   portfolio-service
-   onchain-service
-   sentiment-service

------------------------------------------------------------------------

# 9. Compliance

New services must:

-   Have clear ownership
-   Define APIs
-   Define data ownership
-   Support monitoring
-   Support horizontal scaling

This document defines the official microservice architecture.
