# Integration Test

Version: 1.0

Status: Approved

------------------------------------------------------------------------

# 1. Purpose

Defines system integration testing.

------------------------------------------------------------------------

# 2. Integration Scope

Tests:

-   Services
-   Databases
-   Kafka
-   Cache
-   External APIs

------------------------------------------------------------------------

# 3. Main Flow Test

    Collector

    ↓

    Kafka

    ↓

    Feature

    ↓

    Score

    ↓

    Ranking

    ↓

    Signal

------------------------------------------------------------------------

# 4. Data Validation

Verify:

-   Event format
-   Data consistency
-   Processing result

------------------------------------------------------------------------

# 5. Environment

Executed in staging environment.

------------------------------------------------------------------------

# 6. Compliance

Critical business flows must pass integration tests.
