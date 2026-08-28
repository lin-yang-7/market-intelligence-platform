# FastAPI Architecture

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the FastAPI architecture standard for backend
services of the Market Intelligence Platform.

FastAPI is used as the primary framework for:

-   REST API services
-   WebSocket services
-   Internal service endpoints

------------------------------------------------------------------------

# 2. FastAPI Architecture Principles

The implementation follows:

-   Async First
-   Dependency Injection
-   Layer Separation
-   Type Safety
-   Automatic Documentation
-   High Performance

------------------------------------------------------------------------

# 3. Application Structure

Example:

    app/

    ├── main.py

    ├── api/

    │   ├── routers/

    │   └── dependencies.py

    ├── services/

    ├── repositories/

    ├── schemas/

    ├── models/

    ├── middleware/

    ├── exceptions/

    └── config/

------------------------------------------------------------------------

# 4. Application Lifecycle

FastAPI lifecycle:

    Application Start

    ↓

    Load Configuration

    ↓

    Initialize Database

    ↓

    Initialize Redis

    ↓

    Initialize Kafka

    ↓

    Start Service

Shutdown:

    Stop Requests

    ↓

    Close Connections

    ↓

    Release Resources

------------------------------------------------------------------------

# 5. Router Design

Routers define API endpoints.

Example:

    api/routers/ranking.py

Responsibilities:

-   Receive request
-   Validate parameters
-   Call service
-   Return response

Business logic should not be placed in routers.

------------------------------------------------------------------------

# 6. Dependency Injection

FastAPI Dependency Injection is used for:

-   Authentication
-   Database sessions
-   Redis clients
-   Permission checking

Example:

    Request

    ↓

    Dependency

    ↓

    Service

------------------------------------------------------------------------

# 7. Service Layer

Service layer contains:

-   Business logic
-   Data processing
-   External service calls

Example:

    RankingService

    ↓

    FeatureRepository

    ↓

    ClickHouse

------------------------------------------------------------------------

# 8. Repository Layer

Repository abstracts storage operations.

Examples:

MySQL:

    UserRepository

ClickHouse:

    MarketDataRepository

Redis:

    CacheRepository

------------------------------------------------------------------------

# 9. Middleware

Common middleware:

-   Request ID
-   Authentication
-   Logging
-   Rate limiting
-   CORS

------------------------------------------------------------------------

# 10. Exception Handling

Unified exception system:

Examples:

    AuthenticationError

    ValidationError

    PermissionError

    ServiceError

Response:

``` json
{
 "code":1001,
 "message":"Unauthorized"
}
```

------------------------------------------------------------------------

# 11. Async Programming

Use async for:

-   HTTP requests
-   Database operations
-   Kafka consumers
-   WebSocket handling

Example:

    async def get_signal():
        pass

------------------------------------------------------------------------

# 12. Database Connection Management

Services manage:

MySQL:

-   Connection pool

Redis:

-   Async client pool

ClickHouse:

-   Query client

Connections are initialized during application startup.

------------------------------------------------------------------------

# 13. API Documentation

FastAPI automatically provides:

OpenAPI:

    /docs

Alternative:

    /redoc

Requirements:

-   Endpoint description
-   Parameter description
-   Response schema

------------------------------------------------------------------------

# 14. Request Validation

Use Pydantic models.

Example:

    Request Schema

    ↓

    Validation

    ↓

    Service

Validation includes:

-   Required fields
-   Data type
-   Range checking

------------------------------------------------------------------------

# 15. Security Integration

FastAPI integrates:

-   API Key authentication
-   JWT validation
-   Permission checking

------------------------------------------------------------------------

# 16. Health Check

Every service provides:

    GET /health

Response:

``` json
{
 "status":"ok"
}
```

------------------------------------------------------------------------

# 17. Monitoring Integration

Collect:

-   Request latency
-   Error count
-   Request count
-   Resource usage

------------------------------------------------------------------------

# 18. Testing

Required:

-   Router tests
-   Service tests
-   Repository tests
-   Integration tests

------------------------------------------------------------------------

# 19. Future Extensions

Reserved:

-   GraphQL gateway
-   Service mesh integration
-   Distributed tracing

------------------------------------------------------------------------

# 20. Compliance

Every FastAPI service must define:

-   Router structure
-   Dependency management
-   Exception handling
-   Monitoring
-   Testing

This document defines the official FastAPI architecture standard.
