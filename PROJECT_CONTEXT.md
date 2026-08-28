# Market Intelligence Platform - Project Context

## Project Goal

Build a professional cryptocurrency Market Intelligence Platform similar in capability to ValueScan.

The platform is not a trading bot or exchange. It provides real-time market aggregation, intelligent asset screening, market ranking, trading signals, historical data, public REST APIs, WebSocket APIs, SDKs, and future AI integration.

The platform is designed as a commercial API-first SaaS product.

## Technology Stack

- Backend: Python 3.12, FastAPI
- Databases: MySQL, ClickHouse, Redis
- Message Queue: Apache Kafka
- Frontend: Vue 3, TypeScript
- Deployment: Docker, Kubernetes

## Database Responsibilities

### MySQL

Business data such as users, API keys, subscriptions, alerts, and permissions.

### ClickHouse

Historical analytics such as klines, trades, feature history, and signal history.

### Redis

Hot cache such as latest market data, rankings, signals, and sessions.

## Architecture Principles

- API First
- Event Driven
- Stateless Services
- Database per Service
- Feature Store First
- AI Ready
- Horizontal Scalability

Services communicate through REST APIs and Kafka. Do not access another service's database directly.

## Core Services

- gateway-service
- auth-service
- user-service
- collector-service
- market-service
- history-service
- feature-service
- feature-store-service
- rule-service
- score-service
- screener-service
- ranking-service
- signal-service
- websocket-service
- alert-service
- notification-service

## Core Features

- Market Data
- Feature Engine
- Feature Store
- Ranking
- Screener
- Signal Center
- Alert Center
- REST API
- WebSocket
- Dashboard
- Developer Platform

## API Rules

REST API version:

```text
/v1/
```

Common parameters:

- symbol
- interval
- startTime
- endTime
- limit
- cursor

Response format:

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

Keep APIs backward compatible.

## AI Plan

Version 1 uses the Rule Engine and Feature Store.

Version 2 adds the AI Service and AI Score.

Do not redesign APIs when AI is added.

## Current Status

Architecture and planning are complete. The next step is implementation.

Implement according to the architecture instead of redesigning it.

## Repository

```text
lin-yang-7/market-intelligence-platform
```
