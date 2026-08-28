# System Architecture

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the overall technical architecture of the Market
Intelligence Platform.

It establishes the system structure, technology choices, communication
patterns, storage strategy, scalability model, and engineering
principles.

All future technical documents and implementations must follow this
architecture.

------------------------------------------------------------------------

# 2. Architecture Goals

The architecture must support:

-   High availability
-   Low latency
-   Horizontal scalability
-   Multi-exchange data processing
-   Public API services
-   Real-time streaming
-   Historical analytics
-   Future AI integration
-   Enterprise deployment

------------------------------------------------------------------------

# 3. High Level Architecture

                        Users
                          |
                  API Gateway Layer
                          |
          --------------------------------
          |              |               |
       REST API     WebSocket API      SSE
          |
     Business Service Layer
          |
     -------------------------------------
     |          |          |             |
    Market   Feature    Signal       User
    Service  Service    Service     Service
          |
     Event Streaming Layer
            Kafka
          |
     Collector Services
          |
     Exchanges
     Binance / Bybit / OKX

------------------------------------------------------------------------

# 4. Architecture Layers

## Exchange Layer

Responsible for:

-   Exchange connections
-   WebSocket management
-   Data collection
-   Data normalization

Supported:

-   Binance
-   Bybit
-   OKX

------------------------------------------------------------------------

## Data Processing Layer

Responsible for:

-   Feature calculation
-   Rule evaluation
-   Score generation
-   Signal generation

------------------------------------------------------------------------

## Service Layer

Provides:

-   REST APIs
-   WebSocket APIs
-   User services
-   Business logic

------------------------------------------------------------------------

## Storage Layer

Uses multiple databases based on purpose.

------------------------------------------------------------------------

# 5. Storage Architecture

## MySQL

Purpose:

Business transactions.

Stores:

-   Users
-   API Keys
-   Subscriptions
-   Permissions
-   Alerts
-   Audit Logs

------------------------------------------------------------------------

## ClickHouse

Purpose:

Analytical data.

Stores:

-   Historical market data
-   Trades
-   Klines
-   Features
-   Signals
-   Scores

------------------------------------------------------------------------

## Redis

Purpose:

Real-time cache.

Stores:

-   Latest market data
-   Ranking results
-   Signal cache
-   Sessions
-   WebSocket state

------------------------------------------------------------------------

# 6. Event Driven Architecture

Apache Kafka is the communication backbone.

Main topics:

    market.ticker

    market.trade

    market.kline

    market.depth

    market.funding

    market.open_interest

    feature.updated

    score.updated

    signal.created

    alert.triggered

Events must include:

-   event_id
-   event_type
-   timestamp
-   exchange
-   symbol
-   version
-   payload

------------------------------------------------------------------------

# 7. Core Architecture Principles

## API First

All capabilities must expose APIs.

------------------------------------------------------------------------

## Event Driven

Services communicate asynchronously whenever possible.

------------------------------------------------------------------------

## Database Isolation

Each service owns its data.

No direct cross-service database access.

------------------------------------------------------------------------

## Stateless Services

Services can scale horizontally.

------------------------------------------------------------------------

## Feature Store First

All quantitative features are managed through Feature Store.

------------------------------------------------------------------------

## AI Ready

The architecture supports future AI models without API redesign.

------------------------------------------------------------------------

# 8. Communication Model

## Synchronous

Used for:

-   Authentication
-   User operations
-   Configuration
-   Administration

Protocol:

REST API

------------------------------------------------------------------------

## Asynchronous

Used for:

-   Market events
-   Feature updates
-   Signals
-   Notifications

Protocol:

Kafka

------------------------------------------------------------------------

# 9. Scalability Strategy

Collector:

Scale by exchange.

Feature Engine:

Scale by Kafka partition.

API Services:

Scale by request volume.

WebSocket:

Scale by connection count.

ClickHouse:

Scale by cluster.

MySQL:

Primary and replica.

Redis:

Cluster mode.

------------------------------------------------------------------------

# 10. Security Architecture

Authentication:

-   JWT
-   API Key

Authorization:

-   RBAC

Transport:

-   HTTPS
-   WSS

Secrets:

-   Environment configuration
-   Secret management

------------------------------------------------------------------------

# 11. Observability

Monitoring:

-   Prometheus
-   Grafana

Logging:

-   Loki

Tracing:

-   OpenTelemetry

Every service provides:

-   Health endpoint
-   Metrics endpoint
-   Structured logs

------------------------------------------------------------------------

# 12. Deployment Model

Supported:

-   Local Development
-   Docker Compose
-   Kubernetes
-   Cloud Deployment
-   Private Enterprise Deployment

------------------------------------------------------------------------

# 13. Technology Stack

  Layer           Technology
  --------------- -----------------------
  Backend         Python 3.12 + FastAPI
  Frontend        Vue 3 + TypeScript
  Database        MySQL
  Analytics       ClickHouse
  Cache           Redis
  Message Queue   Kafka
  Container       Docker
  Orchestration   Kubernetes
  Monitoring      Prometheus + Grafana

------------------------------------------------------------------------

# 14. Future Extensions

Reserved:

-   AI Service
-   On-chain Analytics
-   DEX Data
-   Strategy Platform
-   Backtesting Platform
-   LLM Assistant

------------------------------------------------------------------------

# 15. Architecture Compliance

All new modules must:

-   Follow API First design
-   Use defined storage responsibilities
-   Support monitoring
-   Maintain compatibility
-   Avoid unnecessary coupling

This document is the technical foundation of the Market Intelligence
Platform.
