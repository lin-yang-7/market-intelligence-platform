# Core Features

Version: 1.0

Status: Approved

# 1. Purpose

This document defines the complete functional scope of the Market
Intelligence Platform.

It is the primary reference for architecture, database design, API
design, frontend development, and future AI integration.

All features must map to:

-   Service
-   Database Schema
-   API
-   Monitoring Metrics
-   Test Cases

------------------------------------------------------------------------

# 2. Functional Domains

The platform contains the following functional domains:

  ID      Domain
  ------- ---------------------
  F01     Market Data
  F02     Market Intelligence
  F02.1   Feature Store
  F03     Ranking
  F03.1   Screener
  F04     Signal Center
  F05     Alert Center
  F06     User Platform
  F07     API Platform
  F08     Streaming Platform
  F09     Dashboard
  F10     Administration
  F11     Monitoring
  F12     AI Extension
  F13     Developer Platform

------------------------------------------------------------------------

# 3. F01 Market Data

## Objective

Provide normalized real-time market data from multiple exchanges.

## Features

-   Ticker Data
-   Kline Data
-   Trade Data
-   Order Book
-   Funding Rate
-   Open Interest
-   Liquidation Data
-   Exchange Status

## Supported Exchanges

Version 1:

-   Binance
-   Bybit
-   OKX

## Outputs

-   REST API
-   WebSocket
-   Historical Storage
-   Internal Events

------------------------------------------------------------------------

# 4. F02 Market Intelligence

## Objective

Transform raw market data into quantitative market features.

## Feature Categories

-   Trend
-   Momentum
-   Volatility
-   Volume
-   Liquidity
-   Funding
-   Open Interest
-   Market Structure
-   Flow Analysis

## Technical Indicators

-   RSI
-   MACD
-   EMA
-   SMA
-   ATR
-   VWAP

## Advanced Features

-   Volume Ratio
-   Trend Strength
-   Breakout Detection
-   Net Flow
-   Market Score

------------------------------------------------------------------------

# 5. F02.1 Feature Store

## Objective

Provide a centralized feature management system.

The Feature Store is the foundation for ranking, screening, signals, and
future AI models.

## Responsibilities

-   Feature Registry
-   Feature Catalog
-   Feature Metadata
-   Feature Versioning
-   Feature Validation
-   Feature Discovery

## Storage

Online:

-   Redis

Offline:

-   ClickHouse

## Feature Requirements

Every feature must include:

-   Name
-   Description
-   Category
-   Version
-   Calculation Method
-   Update Frequency
-   Data Source
-   Dependencies

## Future Extensions

-   Machine Learning Features
-   AI Features
-   Backtesting Features
-   Research Dataset

------------------------------------------------------------------------

# 6. F03 Ranking

## Objective

Rank assets based on quantitative scores.

## Ranking Types

-   Overall Ranking
-   Long Opportunity
-   Short Opportunity
-   Momentum Ranking
-   Volume Ranking
-   Funding Ranking
-   Open Interest Ranking

## Sorting

-   Score
-   Volume
-   Change
-   Funding
-   Open Interest

------------------------------------------------------------------------

# 7. F03.1 Screener

## Objective

Provide intelligent asset selection through configurable conditions.

## Filter Types

-   Price
-   Volume
-   Funding
-   Open Interest
-   RSI
-   MACD
-   EMA
-   ATR
-   Volume Ratio
-   Net Flow
-   Score
-   Signal

## Logic

Support:

-   AND
-   OR
-   Nested Conditions

## Built-in Templates

-   Long Inflow
-   Breakout
-   Momentum
-   Smart Money
-   High Volume

## User Functions

Users can:

-   Create Screeners
-   Save Screeners
-   Duplicate Screeners
-   Share Screeners
-   Export Results

------------------------------------------------------------------------

# 8. F04 Signal Center

## Objective

Generate standardized market signals.

## Signal Types

-   Long
-   Short
-   Breakout
-   Momentum
-   Reversal
-   Watch

## Signal Data

Contains:

-   Symbol
-   Exchange
-   Timestamp
-   Signal Type
-   Score
-   Confidence
-   Reason
-   Supporting Features

------------------------------------------------------------------------

# 9. F05 Alert Center

## Objective

Notify users when conditions are triggered.

## Alert Types

-   Price Alert
-   Feature Alert
-   Ranking Alert
-   Signal Alert
-   Screener Alert

## Channels

-   Dashboard
-   Email
-   Telegram
-   Webhook

------------------------------------------------------------------------

# 10. Traceability Requirement

Every feature must have:

-   Functional Definition
-   API Definition
-   Database Mapping
-   Service Ownership
-   Monitoring Metrics
-   Test Coverage
