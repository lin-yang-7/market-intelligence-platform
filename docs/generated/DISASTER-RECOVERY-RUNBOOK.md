# Disaster Recovery Runbook

## Scope

This MVP runbook implements the recovery procedure required by
`docs/02-Architecture/10-Disaster-Recovery.md` for a single-node Docker Compose
deployment. It is intentionally non-destructive until an operator runs database
restore commands with a verified backup source.

## Recovery Objectives

- API, WebSocket, collector, and worker services: restore within minutes after
  infrastructure is available.
- MySQL and ClickHouse: restore within hours depending on backup size.
- User/configuration data RPO: latest verified database backup.
- Market and analytics RPO: latest ClickHouse export/snapshot plus Kafka
  replay where available.

## Required Artifacts

Verify required artifacts:

```powershell
python scripts\disaster_recovery_check.py
```

The check validates:

- `deployment/docker-compose.yml`
- `sql/mysql/001_business_baseline.sql`
- `sql/clickhouse/001_market_baseline.sql`
- `docs/generated/BACKUP-RETENTION-PLAN.md`
- `docs/generated/PRODUCTION-DEPLOYMENT-RUNBOOK.md`
- `scripts/check_deployment_health.py`

## Incident Triage

1. Assign an incident ID and owner.
2. Classify impact: service-only, Redis, Kafka, MySQL, ClickHouse, or regional.
3. Preserve logs and failed volumes before restore.
4. Stop write traffic if database restore is required.

## Service-Only Recovery

```powershell
docker compose -f deployment/docker-compose.yml ps
docker compose -f deployment/docker-compose.yml restart api-gateway ranking-service websocket-service
python scripts\check_deployment_health.py
```

If a worker is stuck, restart the specific worker:

```powershell
docker compose -f deployment/docker-compose.yml restart collector-service market-worker feature-worker ranking-monitor-worker data-platform-worker
```

## Database Recovery

1. Stop application and worker services.
2. Restore MySQL from the latest verified full or incremental backup.
3. Restore ClickHouse from the latest verified snapshot/export.
4. Restore Redis AOF/RDB only when session or real-time state is required.
5. Start infrastructure services.
6. Start application services.
7. Run health checks and domain checks.

```powershell
docker compose -f deployment/docker-compose.yml up -d mysql redis zookeeper kafka clickhouse
docker compose -f deployment/docker-compose.yml up -d
python scripts\check_deployment_health.py
```

## Data Validation

After restore, validate these paths:

- `GET http://localhost:8000/ready`
- `GET http://localhost:8000/v1/history/ranking-monitor/events?limit=10`
- `POST http://localhost:8000/v1/ranking/monitor/opportunityBullish?exchange=binance`
- WebSocket subscription to `ranking.strategy`

## Kafka Recovery

1. Restore broker availability.
2. Confirm topics auto-create or exist.
3. Restart consumers:

```powershell
docker compose -f deployment/docker-compose.yml restart market-worker feature-worker data-platform-worker
```

4. Verify `feature.updated` and `ranking.strategy` events continue to flow.

## Regional Recovery

1. Provision a backup host with Docker Compose.
2. Copy configuration and verified backups.
3. Restore databases.
4. Start services.
5. Run `scripts\check_deployment_health.py`.
6. Redirect DNS or upstream traffic only after readiness is green.

## Post-Recovery Review

Record:

- Incident ID
- Timeline
- Root cause
- Data loss estimate
- Restore commands executed
- Follow-up prevention work

## Current Gaps

- Automated backup restore is not implemented.
- Cross-region replication is not implemented.
- Kubernetes automated failover is not implemented.
- Backup encryption and secret rotation need production integration.
