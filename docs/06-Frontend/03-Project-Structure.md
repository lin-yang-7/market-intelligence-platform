# Frontend Project Structure

Version: 1.0

## 1. Purpose

Defines the frontend engineering directory standard.

## 2. Repository Structure

    frontend/

    ├── src/
    ├── public/
    ├── tests/
    ├── package.json
    └── vite.config.ts

## 3. Source Structure

    src/

    ├── api/
    ├── assets/
    ├── components/
    ├── layouts/
    ├── pages/
    ├── router/
    ├── stores/
    ├── hooks/
    ├── websocket/
    ├── types/
    └── utils/

## 4. Module Organization

Business modules:

    modules/

    ├── dashboard/
    ├── ranking/
    ├── signal/
    ├── alert/
    └── market/

Each module contains:

-   pages
-   components
-   api
-   store
-   types

## 5. Component Categories

Common:

-   Button
-   Table
-   Chart
-   Dialog

Business:

-   RankingCard
-   SignalCard
-   AlertPanel
-   MarketChart

## 6. Chart Components

Trading visualization components:

-   Candlestick chart
-   Volume chart
-   Ranking chart
-   Signal timeline

## 7. Configuration

Includes:

-   Environment variables
-   API URL
-   WebSocket URL
-   Feature flags

## 8. Compliance

Every frontend module must maintain clear ownership and independent
structure.
