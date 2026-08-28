# Capacity Baseline

This baseline is the deployment admission checklist for the MVP. Validate it with
`scripts/real_integration_check.py` before changing replicas or collector scope.

| Component | Initial replicas | CPU request/limit | Memory request/limit | Scale signal |
| --- | ---: | --- | --- | --- |
| API Gateway | 2 | 100m / 500m | 256Mi / 512Mi | p95 latency > 500ms |
| Market / Feature / Ranking | 2 | 100m / 500m | 256Mi / 512Mi | backlog or p95 latency > 500ms |
| Workers | 1 | 100m / 500m | 256Mi / 512Mi | Kafka consumer lag |
| ClickHouse | 1 | environment sized | environment sized | disk > 70% or query latency |
| Redis | 1 | environment sized | environment sized | memory > 70% or eviction |

Run a 100-request, 10-concurrency gateway probe before release. Increase load in
approved staging only; record p50, p95, Kafka lag, Redis memory, ClickHouse disk,
and error rate for each run.
