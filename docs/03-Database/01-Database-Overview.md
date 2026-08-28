# Database Overview

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the database architecture overview of the Market
Intelligence Platform.

The platform uses a polyglot persistence architecture.

Different storage engines are selected according to data
characteristics.

------------------------------------------------------------------------

# 2. Database Architecture Principles

The database design follows:

-   Database per Service
-   Clear Data Ownership
-   High Performance
-   Scalability
-   Data Consistency
-   Easy Maintenance

No service should directly access another service's database.

------------------------------------------------------------------------

# 3. Storage System Overview

The platform uses three primary storage systems.

  Storage      Purpose
  ------------ -----------------
  MySQL        Business Data
  ClickHouse   Analytical Data
  Redis        Real-time Cache

------------------------------------------------------------------------

# 4. MySQL Role

## Purpose

MySQL stores transactional and business-related information.

Suitable for:

-   User management
-   Permission management
-   Subscription management
-   Configuration management

------------------------------------------------------------------------

## Stored Data

Examples:

Users

API Keys

Subscriptions

Permissions

Alerts

Organizations

Audit Logs

System Configuration

------------------------------------------------------------------------

## Characteristics

-   ACID transactions
-   Relational model
-   Strong consistency
-   Business operations

------------------------------------------------------------------------

# 5. ClickHouse Role

## Purpose

ClickHouse stores high-volume analytical and time-series data.

Suitable for:

-   Market history
-   Quantitative analysis
-   Feature analysis
-   Research

------------------------------------------------------------------------

## Stored Data

Market:

-   Trades
-   Klines
-   Funding
-   Open Interest
-   Liquidations

Intelligence:

-   Features
-   Scores
-   Signals

------------------------------------------------------------------------

## Characteristics

-   Column storage
-   High compression
-   Fast aggregation
-   Large-scale analytics

------------------------------------------------------------------------

# 6. Redis Role

## Purpose

Redis provides high-speed access for real-time applications.

------------------------------------------------------------------------

## Stored Data

Examples:

-   Latest ticker
-   Ranking results
-   Feature snapshots
-   Signal cache
-   User sessions
-   WebSocket states

------------------------------------------------------------------------

## Characteristics

-   Low latency
-   Memory based
-   High throughput

------------------------------------------------------------------------

# 7. Data Classification

## Transaction Data

Storage:

MySQL

Examples:

-   Users
-   Orders
-   Permissions

------------------------------------------------------------------------

## Real-time Data

Storage:

Redis

Examples:

-   Latest price
-   Current ranking

------------------------------------------------------------------------

## Historical Data

Storage:

ClickHouse

Examples:

-   Market history
-   Features
-   Signals

------------------------------------------------------------------------

# 8. Data Flow

    Exchange

    ↓

    Collector

    ↓

    Kafka

    ↓

    Processing Services

    ↓

    Redis / MySQL / ClickHouse

------------------------------------------------------------------------

# 9. Data Ownership Rules

Each service owns its data.

Example:

User Service:

Owns:

-   users
-   api_keys
-   subscriptions

Feature Store Service:

Owns:

-   feature metadata
-   feature versions

Signal Service:

Owns:

-   signals

------------------------------------------------------------------------

# 10. Data Access Rules

Correct:

    Service

    ↓

    Own Database

Incorrect:

    Service A

    ↓

    Database of Service B

------------------------------------------------------------------------

# 11. Backup Strategy

MySQL:

-   Full backup
-   Incremental backup

ClickHouse:

-   Snapshot
-   Replication

Redis:

-   RDB
-   AOF

------------------------------------------------------------------------

# 12. Data Retention

Business Data:

Long-term retention

Historical Data:

Based on storage policy

Cache Data:

TTL controlled

------------------------------------------------------------------------

# 13. Security Requirements

Database access requires:

-   Authentication
-   Authorization
-   Network isolation
-   Audit logging

------------------------------------------------------------------------

# 14. Future Extensions

Reserved:

-   Data Warehouse
-   Data Lake
-   Feature Platform
-   Real-time Analytics Engine

------------------------------------------------------------------------

# 15. Compliance

Every new database table must define:

-   Owner Service
-   Purpose
-   Schema
-   Index Strategy
-   Retention Policy
-   Backup Policy

This document defines the database foundation of the platform.
