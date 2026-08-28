# Backend Project Structure

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

This document defines the backend project structure standard for the
Market Intelligence Platform.

The goal is to provide:

-   Clear service boundaries
-   Maintainable code structure
-   Scalable development workflow
-   Consistent engineering standards

------------------------------------------------------------------------

# 2. Repository Structure

Recommended:

    market-intelligence-platform/

    ├── backend/

    ├── frontend/

    ├── ai-engine/

    ├── data-platform/

    ├── infrastructure/

    ├── docs/

    └── tests/

------------------------------------------------------------------------

# 3. Backend Directory

    backend/

    ├── services/

    ├── common/

    ├── libraries/

    ├── migrations/

    ├── scripts/

    ├── tests/

    └── docker/

------------------------------------------------------------------------

# 4. Service Structure

Each microservice follows:

    service-name/

    ├── app/

    │   ├── api/

    │   ├── services/

    │   ├── repositories/

    │   ├── models/

    │   ├── schemas/

    │   ├── workers/

    │   ├── config/

    │   └── main.py

    │

    ├── tests/

    ├── Dockerfile

    ├── requirements.txt

    └── README.md

------------------------------------------------------------------------

# 5. Layer Responsibilities

## API Layer

Location:

    app/api/

Responsibilities:

-   HTTP endpoints
-   Request validation
-   Response formatting

------------------------------------------------------------------------

## Service Layer

Location:

    app/services/

Responsibilities:

-   Business logic
-   Workflow processing
-   Service coordination

------------------------------------------------------------------------

## Repository Layer

Location:

    app/repositories/

Responsibilities:

-   Database operations
-   Data access abstraction

------------------------------------------------------------------------

## Model Layer

Location:

    app/models/

Responsibilities:

-   ORM models
-   Database entities

------------------------------------------------------------------------

## Schema Layer

Location:

    app/schemas/

Responsibilities:

-   Request models
-   Response models

Technology:

Pydantic

------------------------------------------------------------------------

# 6. Example Service

Example:

    ranking-service/

    app/

    ├── api/

    │   └── ranking.py

    ├── services/

    │   └── ranking_engine.py

    ├── repositories/

    │   └── ranking_repository.py

    ├── models/

    │   └── ranking.py

    ├── schemas/

    │   └── ranking_schema.py

    └── main.py

------------------------------------------------------------------------

# 7. Common Components

Directory:

    common/

Contains:

-   Logger
-   Exception handling
-   Authentication
-   Database connection
-   Kafka client
-   Redis client
-   Utilities

------------------------------------------------------------------------

# 8. Configuration Management

Structure:

    config/

    ├── settings.py

    ├── database.py

    ├── kafka.py

    └── redis.py

Configuration source:

-   Environment variables
-   Secret manager

------------------------------------------------------------------------

# 9. Database Migration

Directory:

    migrations/

Contains:

-   MySQL migration
-   ClickHouse migration

Tools:

-   Alembic
-   Flyway

------------------------------------------------------------------------

# 10. Background Workers

Used for:

-   Kafka consumers
-   Data processing
-   Scheduled tasks

Directory:

    workers/

------------------------------------------------------------------------

# 11. Testing Structure

Example:

    tests/

    ├── unit/

    ├── integration/

    ├── api/

    └── performance/

------------------------------------------------------------------------

# 12. Development Standards

All services require:

-   README
-   Dockerfile
-   Health endpoint
-   Logging
-   Tests
-   Configuration documentation

------------------------------------------------------------------------

# 13. Docker Structure

Example:

    docker/

    ├── Dockerfile

    ├── docker-compose.yml

    └── scripts/

------------------------------------------------------------------------

# 14. CI/CD Integration

Pipeline:

    Code Commit

    ↓

    Test

    ↓

    Build Image

    ↓

    Security Scan

    ↓

    Deploy

------------------------------------------------------------------------

# 15. Future Extensions

Reserved:

-   Kubernetes Helm charts
-   Service mesh
-   Multi-region deployment

------------------------------------------------------------------------

# 16. Compliance

Every backend project must follow:

-   Directory standard
-   Layer separation
-   Testing requirements
-   Deployment requirements

This document defines the official backend project structure.
