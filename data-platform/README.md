# Data Platform

The Data Platform defines the local processing contract and production-facing
data engineering jobs for incoming events:

- validate event shape and quality
- normalize payloads for downstream storage
- route events to ClickHouse analytical tables
- expose a lightweight internal API for pipeline diagnostics
- run stream-style window aggregation jobs
- run batch symbol feature rollups
- produce warehouse layer plans
- write partitioned JSONL data lake files
- report freshness, delay, and event-loss suspicion
- build governance ownership and lineage graphs

## Local Run

```powershell
$env:PYTHONPATH='backend/common;data-platform'
uvicorn data_platform.app.main:app --host 0.0.0.0 --port 8011
```

## API

- `GET /health`
- `POST /v1/data/validate`
- `POST /v1/data/quality/report`
- `POST /v1/data/stream/process`
- `POST /v1/data/batch/run`
- `POST /v1/data/warehouse/plan`
- `POST /v1/data/lake/write`
- `POST /v1/data/freshness/report`
- `POST /v1/data/governance/lineage`
- `POST /v1/data/route`
- `POST /v1/data/process`
