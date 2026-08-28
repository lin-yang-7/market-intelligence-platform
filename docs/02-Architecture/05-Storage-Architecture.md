# Storage Architecture

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the storage architecture of the Market
Intelligence Platform.

The platform uses multiple storage systems based on different data
characteristics.

Storage selection follows:

-   Business data → MySQL
-   Analytical data → ClickHouse
-   Real-time data → Redis

------------------------------------------------------------------------

# 2. Storage Overview

                     Application Services

                             |

            ---------------------------------

            |               |               |

          MySQL         ClickHouse        Redis

       Business       Analytics        Real-time

------------------------------------------------------------------------

# 3. MySQL Architecture

## Purpose

MySQL stores transactional and business-related data.

## Owned Data

-   Users
-   Organizations
-   API Keys
-   Permissions
-   Subscriptions
-   Alerts
-   Configuration
-   Audit Logs

------------------------------------------------------------------------

## Design Principles

MySQL should store:

-   Structured business entities
-   User operations
-   Transactional records

MySQL should not store:

-   High-frequency market ticks
-   Large historical time-series data

------------------------------------------------------------------------

## Schema Strategy

Each business domain owns its tables.

Examples:

User Domain:

    users

    user_profiles

    api_keys

    subscriptions

Alert Domain:

    alert_rules

    alert_history

------------------------------------------------------------------------

# 4. ClickHouse Architecture

## Purpose

ClickHouse is the analytical database.

It stores large-scale time-series and analytical data.

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

## Table Design Principles

Use:

-   Partitioning
-   Ordering keys
-   Compression
-   Batch insertion

Avoid:

-   Frequent updates
-   Transaction-heavy operations

------------------------------------------------------------------------

## Partition Strategy

Primary partition:

    date

Sorting keys:

    exchange

    symbol

    timestamp

------------------------------------------------------------------------

# 5. Redis Architecture

## Purpose

Redis provides low-latency access.

------------------------------------------------------------------------

## Cached Data

Market:

    ticker:{symbol}

    depth:{symbol}

Ranking:

    ranking:{type}

Signals:

    signal:latest

Sessions:

    session:{id}

------------------------------------------------------------------------

## Cache Strategy

Patterns:

-   Cache Aside
-   Write Through
-   Expiration Control

------------------------------------------------------------------------

# 6. Data Lifecycle

## Real-Time Data

Examples:

-   Price
-   Order Book
-   Ranking

Storage:

Redis

Retention:

Seconds to hours

------------------------------------------------------------------------

## Business Data

Examples:

-   Users
-   API Keys

Storage:

MySQL

Retention:

Long term

------------------------------------------------------------------------

## Historical Data

Examples:

-   Klines
-   Features
-   Signals

Storage:

ClickHouse

Retention:

According to data policy

------------------------------------------------------------------------

# 7. Data Access Rules

Services must access storage according to ownership.

Example:

Correct:

    API

    ↓

    Market Service

    ↓

    Redis

Incorrect:

    API

    ↓

    Direct Redis Access

------------------------------------------------------------------------

# 8. Backup Strategy

## MySQL

Backup:

-   Daily full backup
-   Incremental backup

------------------------------------------------------------------------

## ClickHouse

Backup:

-   Snapshot
-   Replication

------------------------------------------------------------------------

## Redis

Backup:

-   RDB
-   AOF

------------------------------------------------------------------------

# 9. High Availability

## MySQL

Deployment:

-   Primary
-   Replica

------------------------------------------------------------------------

## ClickHouse

Deployment:

-   Cluster
-   Replication

------------------------------------------------------------------------

## Redis

Deployment:

-   Sentinel
-   Cluster

------------------------------------------------------------------------

# 10. Performance Requirements

MySQL:

-   Optimize transactional queries
-   Proper indexing

ClickHouse:

-   Optimize analytical queries
-   Partition pruning

Redis:

-   Low latency access
-   Controlled memory usage

------------------------------------------------------------------------

# 11. Future Extensions

Reserved:

-   Data Warehouse
-   Data Lake
-   Object Storage
-   Real-time OLAP
-   Feature Store Platform

------------------------------------------------------------------------

# 12. Compliance

All new storage requirements must define:

-   Data owner
-   Storage engine
-   Schema
-   Retention policy
-   Backup strategy
-   Access method

This document defines the official storage architecture.
