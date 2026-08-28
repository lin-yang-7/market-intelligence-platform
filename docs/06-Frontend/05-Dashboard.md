# Dashboard Design

Version: 1.0

## 1. Purpose

Defines the main market intelligence dashboard.

## 2. Dashboard Goal

Provide:

-   Market overview
-   Opportunity discovery
-   Real-time monitoring

## 3. Page Structure

    Dashboard

    ├── Market Summary
    ├── Ranking Panel
    ├── Signal Feed
    ├── Alert Panel
    └── Charts

## 4. Market Summary

Displays:

-   Total market status
-   Volume
-   Trend
-   Volatility

## 5. Ranking Panel

Shows:

-   Top coins
-   Long inflow ranking
-   Momentum ranking

## 6. Signal Feed

Displays:

-   New signals
-   Score
-   Confidence
-   Explanation

## 7. Real-time Update

Uses:

WebSocket events:

-   ranking.updated
-   signal.created
-   alert.triggered

## 8. Performance

Optimization:

-   Lazy loading
-   Virtual lists
-   Data caching

## 9. Compliance

Dashboard modules must define data source and refresh strategy.
