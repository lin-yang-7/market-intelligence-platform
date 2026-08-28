# Database Index Strategy

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines indexing and query optimization strategies for the
Market Intelligence Platform.

The goal is to maintain high performance for transactional queries,
analytical queries, and real-time access.

------------------------------------------------------------------------

# 2. Index Design Principles

All indexes should follow:

-   Based on query patterns
-   Avoid unnecessary indexes
-   Monitor index effectiveness
-   Balance read and write performance
-   Review periodically

------------------------------------------------------------------------

# 3. MySQL Index Strategy

## Primary Key

All business tables require a primary key.

Recommended:

    id

Type:

-   BIGINT
-   UUID

------------------------------------------------------------------------

# 4. Common MySQL Indexes

## User Queries

Table:

    users

Indexes:

    PRIMARY KEY(id)

    UNIQUE(email)

    INDEX(status)

Purpose:

-   Login lookup
-   Account status filtering

------------------------------------------------------------------------

## API Key Queries

Table:

    api_keys

Indexes:

    UNIQUE(api_key)

    INDEX(user_id)

    INDEX(status)

Purpose:

-   Authentication
-   User API management

------------------------------------------------------------------------

## Subscription Queries

Table:

    subscriptions

Indexes:

    INDEX(user_id)

    INDEX(status)

    INDEX(end_time)

Purpose:

-   Subscription validation

------------------------------------------------------------------------

## Alert Queries

Table:

    alert_rules

Indexes:

    INDEX(user_id)

    INDEX(enabled)

    INDEX(rule_type)

Purpose:

-   Alert execution

------------------------------------------------------------------------

# 5. Composite Index Strategy

Composite indexes should match query order.

Example:

Query:

``` sql
WHERE user_id=? 
AND status=?
```

Index:

    (user_id,status)

Avoid:

    (status,user_id)

when user_id is the main filter.

------------------------------------------------------------------------

# 6. Time-Based Index Strategy

For tables with time queries:

Example:

    alert_history

Use:

    (created_at)

Purpose:

-   Recent data query
-   History filtering

------------------------------------------------------------------------

# 7. ClickHouse Query Optimization

ClickHouse does not use traditional indexes.

Optimization depends on:

-   Partition
-   Order Key
-   Data skipping indexes

------------------------------------------------------------------------

# 8. ClickHouse Order Key

Recommended:

    (exchange,symbol,timestamp)

Benefits:

-   Fast symbol lookup
-   Time range filtering
-   Data locality

------------------------------------------------------------------------

# 9. ClickHouse Partition Strategy

Partition:

    toYYYYMM(timestamp)

Benefits:

-   Faster scans
-   Data lifecycle management
-   Efficient deletion

------------------------------------------------------------------------

# 10. ClickHouse Data Skipping Indexes

Use when necessary:

Examples:

-   Bloom filter
-   MinMax index

Suitable for:

-   High-cardinality fields
-   Filtering fields

------------------------------------------------------------------------

# 11. Redis Query Optimization

Redis does not use indexes.

Optimization uses:

-   Key design
-   Data structure selection
-   TTL control

------------------------------------------------------------------------

# 12. Redis Data Structures

String:

Used for:

-   Latest price
-   Feature value

Hash:

Used for:

-   Object data

Sorted Set:

Used for:

-   Rankings

List/Stream:

Used for:

-   Event queues

------------------------------------------------------------------------

# 13. High Frequency Query Optimization

Priority:

1.  Redis

2.  MySQL cache

3.  ClickHouse

Example:

Market ranking:

    Request

    ↓

    Redis

    ↓

    Ranking Service

    ↓

    ClickHouse

------------------------------------------------------------------------

# 14. Slow Query Management

Monitor:

MySQL:

-   Slow query log
-   Query execution time

ClickHouse:

-   Query duration
-   Memory usage

Redis:

-   Command latency

------------------------------------------------------------------------

# 15. Index Maintenance

Regular tasks:

-   Review unused indexes
-   Analyze query plans
-   Optimize tables
-   Monitor storage impact

------------------------------------------------------------------------

# 16. Future Extensions

Reserved:

-   Automated index recommendation
-   Query optimizer service
-   Distributed SQL optimization

------------------------------------------------------------------------

# 17. Compliance

Every new table must define:

-   Query patterns
-   Index requirements
-   Performance targets
-   Monitoring metrics

This document defines the database indexing standard.
