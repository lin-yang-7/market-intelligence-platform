# Docker Integration Test Runbook

## Scope

The Docker integration MVP validates that the shared service image can be built
from `backend/Dockerfile.service`, started through Docker Compose, and verified
through `/ready`.

## Static Check

Used by local CI when Docker is unavailable:

```powershell
python scripts\docker_integration_test.py --mode static
```

## Full Docker Check

Requires Docker Engine and Docker Compose:

```powershell
python scripts\docker_integration_test.py --mode full --service auth-service
```

The MVP uses `auth-service` because it has no Redis, Kafka, MySQL, or ClickHouse
dependency. This keeps the integration test fast while still validating:

- Dockerfile build
- Docker Compose service startup
- Python package import path
- Uvicorn process startup
- `/ready` readiness endpoint

## CI

The GitHub Actions Docker job runs the full Docker check.

## Remaining Work

- Full-stack Docker integration with Redis, Kafka, ClickHouse, and MySQL.
- Seeded end-to-end market event flow through Docker Compose.
- Artifact collection for container logs on failure.
