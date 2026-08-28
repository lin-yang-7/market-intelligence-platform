# Data Flow Architecture

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the complete data flow architecture of the Market
Intelligence Platform.

It describes how data moves from external exchanges through collection,
processing, storage, intelligence generation, and external delivery.

------------------------------------------------------------------------

# 2. Data Flow Overview

    Exchange APIs

          |

    Collector Services

          |

    Kafka Event Platform

          |

    +----------------------------+

    |                            |

    Market Service          Feature Service

    |                            |

    Redis                 Feature Store

                                 |

                           Rule Engine

                                 |

                           Signal Engine

                                 |

                      API / WebSocket / Dashboard

                                 |

                           ClickHouse
                        Historical Storage

------------------------------------------------------------------------

# 3. Market Data Flow

## Step 1: Exchange Collection

Collector services connect to:

-   Binance
-   Bybit
-   OKX

Collected data:

-   Ticker
-   Trades
-   Klines
-   Order Book
-   Funding
-   Open Interest

------------------------------------------------------------------------

## Step 2: Data Normalization

Exchange-specific formats are converted into a unified internal format.

Normalized fields:

-   Exchange
-   Symbol
-   Timestamp
-   Price
-   Volume
-   Event Type
-   Version

------------------------------------------------------------------------

## Step 3: Event Publishing

Normalized data is published to Kafka.

Example:

    market.ticker
    market.trade
    market.kline

------------------------------------------------------------------------

# 4. Real-Time Processing Flow

## Market Service

Consumes:

    market.*

Purpose:

-   Update Redis cache
-   Provide low latency APIs

------------------------------------------------------------------------

## Feature Service

Consumes:

    market.*

Purpose:

-   Calculate indicators
-   Generate quantitative features

Outputs:

    feature.updated

------------------------------------------------------------------------

## Rule Service

Consumes:

    feature.updated

Purpose:

-   Evaluate trading conditions
-   Generate scores

Outputs:

    score.updated

------------------------------------------------------------------------

## Signal Service

Consumes:

    score.updated

Purpose:

-   Generate market signals

Outputs:

    signal.created

------------------------------------------------------------------------

# 5. Historical Data Flow

All important market events are archived.

Storage:

## ClickHouse

Stores:

-   Trades
-   Klines
-   Funding
-   Open Interest
-   Features
-   Scores
-   Signals

Purpose:

-   Analytics
-   Research
-   Backtesting
-   Historical APIs

------------------------------------------------------------------------

# 6. User Data Flow

User operations use synchronous APIs.

Flow:

    Client

     |

    API Gateway

     |

    User Service

     |

    MySQL

Examples:

-   Registration
-   Login
-   Subscription
-   API Key Management

------------------------------------------------------------------------

# 7. API Data Flow

External request:

    Client

     |

    API Gateway

     |

    Business Service

     |

    Redis / MySQL / ClickHouse

     |

    Response

Rules:

-   API Gateway handles authentication
-   Services handle business logic
-   Storage access remains internal

------------------------------------------------------------------------

# 8. WebSocket Data Flow

Real-time delivery:

    Kafka

     |

    WebSocket Service

     |

    Connected Clients

Channels:

-   ticker
-   ranking
-   feature
-   signal
-   alert

------------------------------------------------------------------------

# 9. Data Lifecycle

## Real-Time Data

Lifetime:

Seconds to minutes

Storage:

Redis

------------------------------------------------------------------------

## Operational Data

Lifetime:

Months to years

Storage:

MySQL

------------------------------------------------------------------------

## Analytical Data

Lifetime:

Unlimited based on retention policy

Storage:

ClickHouse

------------------------------------------------------------------------

# 10. Data Quality Control

Validation stages:

## Collector Level

Check:

-   Connection status
-   Data format
-   Missing fields

## Processing Level

Check:

-   Calculation errors
-   Duplicate events
-   Timestamp accuracy

## Storage Level

Check:

-   Completeness
-   Consistency

------------------------------------------------------------------------

# 11. Data Latency Targets

Collector:

\< 1 second

Kafka Processing:

milliseconds level

Feature Calculation:

\< 60 seconds

Signal Generation:

\< 3 seconds after feature update

API Response:

\< 50ms cached

------------------------------------------------------------------------

# 12. Data Recovery

Recovery mechanisms:

-   Kafka replay
-   Database backup
-   Event reprocessing
-   Cache rebuild

------------------------------------------------------------------------

# 13. Data Security

Requirements:

-   Encryption in transit
-   Access control
-   Audit logging
-   Sensitive data protection

------------------------------------------------------------------------

# 14. Future Extensions

Reserved:

-   Real-time stream processing
-   AI feature pipeline
-   Data warehouse
-   Data lake
-   Cross-market analytics

------------------------------------------------------------------------

# 15. Compliance

All new data pipelines must define:

-   Source
-   Processing logic
-   Storage destination
-   Ownership
-   Monitoring

This document defines the standard data flow of the platform.
