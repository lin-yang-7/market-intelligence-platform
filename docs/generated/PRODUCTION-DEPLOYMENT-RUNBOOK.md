# Production Deployment Runbook

## Scope

This runbook covers the current Docker Compose deployment path for the Market
Intelligence Platform MVP. Kubernetes, CI/CD, Prometheus, and Grafana remain
separate implementation tracks.

## Required Hosts

- Docker Engine with Docker Compose.
- At least 4 CPU cores and 8 GB RAM for an internal single-node deployment.
- Outbound access to Binance if `collector-service` uses the Binance connector.

## Configure

Set production secrets through environment variables before startup:

```powershell
$env:JWT_SECRET=(.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))")
$env:NOTIFICATION_WEBHOOK_URL=""
$env:TELEGRAM_BOT_TOKEN=""
$env:TELEGRAM_CHAT_ID=""
```

Review `deployment/docker-compose.yml` for ports and service URLs.

## Start

```powershell
docker compose -f deployment/docker-compose.yml up -d --build
```

For registry-based deployment, set `SERVICE_IMAGE` and use the production
override:

```powershell
$env:SERVICE_IMAGE="ghcr.io/OWNER/REPO/market-intelligence-service:TAG"
docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.prod.yml up -d
```

## Verify

Run the readiness check from the repository root:

```powershell
python scripts\check_deployment_health.py
```

For a gateway-only check:

```powershell
python scripts\check_deployment_health.py --base-url http://localhost:8000
```

Each HTTP service exposes:

- `GET /health` for process liveness.
- `GET /ready` for readiness.
- `GET /metrics` for Prometheus-format MVP metrics.

## Smoke Checks

```powershell
python -m pytest backend\tests\test_ranking_service.py backend\tests\test_history_api.py
npm run build --prefix frontend
```

## Rollback

```powershell
docker compose -f deployment/docker-compose.yml down
docker compose -f deployment/docker-compose.yml up -d
```

If schema changes caused issues, restore ClickHouse/MySQL volumes from backup
before restarting services.

## Operational Checks

- API Gateway: `http://localhost:8000/ready`
- WebSocket Service: `http://localhost:8008/ready`
- Data Platform: `http://localhost:8011/ready`
- Ranking Monitor events: `GET /v1/history/ranking-monitor/events`

## Known Remaining Gaps

- Docker integration test is not yet automated in CI.
- Helm chart is not yet implemented.
- CD requires GitHub environment secrets and manual approval.
