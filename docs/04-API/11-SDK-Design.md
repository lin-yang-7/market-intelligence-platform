# SDK Design

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the SDK architecture for the Market Intelligence
Platform API.

SDKs provide convenient access for external developers and enterprise
customers.

Supported languages:

-   Python
-   Node.js
-   Go
-   Java

------------------------------------------------------------------------

# 2. SDK Design Goals

SDKs provide:

-   Simple API access
-   Authentication handling
-   Request signing
-   Error handling
-   Automatic retry
-   WebSocket support

------------------------------------------------------------------------

# 3. SDK Architecture

    Application

    ↓

    SDK Client

    ↓

    API Gateway

    ↓

    Platform API

------------------------------------------------------------------------

# 4. Python SDK

Package:

    market-intelligence-sdk

Example:

``` python
from market_intelligence import Client

client = Client(
    api_key="xxx",
    secret="xxx"
)

result = client.ranking.long_inflow()

print(result)
```

------------------------------------------------------------------------

# 5. Node.js SDK

Package:

    @market-intelligence/sdk

Example:

``` javascript
const client = new Client({
 apiKey:"xxx",
 secret:"xxx"
});

client.signal.current()
```

------------------------------------------------------------------------

# 6. Go SDK

Package:

    github.com/platform/sdk-go

Provides:

-   API Client
-   WebSocket Client
-   Authentication

------------------------------------------------------------------------

# 7. SDK Directory Structure

Example:

    sdk/

    ├── client

    ├── auth

    ├── market

    ├── feature

    ├── ranking

    ├── screener

    ├── signal

    ├── alert

    └── websocket

------------------------------------------------------------------------

# 8. Authentication Module

SDK automatically handles:

-   API Key injection
-   Signature generation
-   Timestamp generation
-   Request headers

------------------------------------------------------------------------

# 9. REST Client

Functions:

-   GET
-   POST
-   DELETE

Features:

-   Timeout control
-   Retry
-   Error parsing
-   Request ID tracking

------------------------------------------------------------------------

# 10. WebSocket Client

Provides:

-   Connection management
-   Authentication
-   Subscribe
-   Unsubscribe
-   Reconnect

Example:

``` python
client.ws.subscribe(
    "signal.created",
    callback
)
```

------------------------------------------------------------------------

# 11. Error Handling

SDK converts API errors into exceptions.

Example:

    AuthenticationError

    RateLimitError

    ParameterError

    ServerError

------------------------------------------------------------------------

# 12. Retry Strategy

SDK supports:

-   Network retry
-   Timeout retry
-   Rate limit backoff

Uses:

-   Exponential backoff

------------------------------------------------------------------------

# 13. Version Management

SDK versions align with API versions.

Example:

    API v1

    SDK 1.x

Breaking API changes require new SDK major versions.

------------------------------------------------------------------------

# 14. Documentation

SDK provides:

-   Installation guide
-   API examples
-   Authentication examples
-   WebSocket examples
-   Error handling guide

------------------------------------------------------------------------

# 15. Testing

SDK requires:

-   Unit tests
-   Integration tests
-   API compatibility tests

------------------------------------------------------------------------

# 16. Future Extensions

Reserved:

-   Trading SDK
-   AI Assistant SDK
-   Strategy SDK
-   Enterprise SDK

------------------------------------------------------------------------

# 17. Compliance

Every SDK must define:

-   Supported APIs
-   Authentication
-   Error handling
-   Version compatibility
-   Usage examples

This document defines the official SDK architecture.
