# Market Intelligence Platform

API-first cryptocurrency market intelligence platform.

The implementation follows the architecture and delivery baseline in [docs/](docs/).
Root-level files are convenience entry points; when details conflict, use the
documentation under `docs/` as the source of truth.

## Current Status

- Documentation baseline is complete.
- Backend MVP services are in place for market, feature, ranking, signal, alert,
  screener, auth, gateway, WebSocket, AI Engine, and Data Platform.
- Frontend MVP includes dashboard, long inflow, ranking, signal, and alert pages.
- Docker assets are present for later integration, but local development can run
  without Docker.

## Repository Structure

```text
docs/
backend/
frontend/
ai-engine/
data-platform/
deployment/
lite/
scripts/
sql/
```

## Lite 部署

仅保留行情采集、特征、评分、排行、信号和前端展示的独立部署包位于
[lite/](lite/)。部署环境、变量和启动方法见 [lite/README.md](lite/README.md)。

## Local Development

Start infrastructure:

```powershell
docker compose -f deployment/docker-compose.yml up -d
```

Check service readiness:

```powershell
python scripts\check_deployment_health.py
```

Deployment runbook: [docs/generated/PRODUCTION-DEPLOYMENT-RUNBOOK.md](docs/generated/PRODUCTION-DEPLOYMENT-RUNBOOK.md).

Check disaster recovery readiness:

```powershell
python scripts\disaster_recovery_check.py
```

Disaster recovery runbook: [docs/generated/DISASTER-RECOVERY-RUNBOOK.md](docs/generated/DISASTER-RECOVERY-RUNBOOK.md).

CI/CD MVP runbook: [docs/generated/CI-CD-MVP-RUNBOOK.md](docs/generated/CI-CD-MVP-RUNBOOK.md).

Logging MVP runbook: [docs/generated/LOGGING-MVP-RUNBOOK.md](docs/generated/LOGGING-MVP-RUNBOOK.md).

Kubernetes MVP runbook: [docs/generated/KUBERNETES-MVP-RUNBOOK.md](docs/generated/KUBERNETES-MVP-RUNBOOK.md).

Monitoring MVP runbook: [docs/generated/MONITORING-MVP-RUNBOOK.md](docs/generated/MONITORING-MVP-RUNBOOK.md).

Docker integration test runbook: [docs/generated/DOCKER-INTEGRATION-TEST-RUNBOOK.md](docs/generated/DOCKER-INTEGRATION-TEST-RUNBOOK.md).

Secret encryption MVP runbook: [docs/generated/SECRET-ENCRYPTION-MVP-RUNBOOK.md](docs/generated/SECRET-ENCRYPTION-MVP-RUNBOOK.md).

Security test MVP runbook: [docs/generated/SECURITY-TEST-MVP-RUNBOOK.md](docs/generated/SECURITY-TEST-MVP-RUNBOOK.md).

Data quality report API MVP: [docs/generated/DATA-QUALITY-REPORT-API-MVP.md](docs/generated/DATA-QUALITY-REPORT-API-MVP.md).

Data Platform full MVP: [docs/generated/DATA-PLATFORM-FULL-MVP.md](docs/generated/DATA-PLATFORM-FULL-MVP.md).

Admin console MVP: [docs/generated/ADMIN-CONSOLE-MVP.md](docs/generated/ADMIN-CONSOLE-MVP.md).

Run the Market API:

```powershell
$env:PYTHONPATH="backend;backend/common"
uvicorn services.market_service.app.main:app --app-dir backend --reload
```

Run the AI Engine:

```powershell
$env:PYTHONPATH="backend/common;ai-engine"
uvicorn ai_engine.app.main:app --reload --port 8010
```

Run the Data Platform API:

```powershell
$env:PYTHONPATH="backend/common;data-platform"
uvicorn data_platform.app.main:app --reload --port 8011
```

Run the collector:

```powershell
$env:PYTHONPATH="backend;backend/common"
python -m services.collector_service.app.main
```

Backfill historical Binance spot K-lines into ClickHouse (default: 90 days of 1-hour candles):

```powershell
$env:PYTHONPATH="backend;backend/common"
python scripts\backfill_binance_klines.py --symbols BTCUSDT,ETHUSDT --interval 1h --days 90
```

The task is safe to rerun: existing candle timestamps are skipped. It only imports source K-lines;
historical features, scores, and signals require their own recalculation jobs.

Backfill every active Binance USDT spot market, ordered by 24-hour quote volume. The checkpoint file
allows a stopped job to resume safely:

```powershell
$env:PYTHONPATH="backend;backend/common;scripts"
python scripts\backfill_binance_market.py --interval 1h --days 90
```

For a broad real-time ticker feed, set `COLLECTOR_AUTO_TOP_SYMBOLS` to a positive value (for example
`50`). Funding, open interest, and liquidation polling remains limited to `COLLECTOR_SYMBOLS` to stay
within exchange API limits.

Set `COLLECTOR_DERIVATIVES_TOP_SYMBOLS` to extend lower-frequency Funding, Open Interest, and
liquidation collection to the most-liquid USDT markets; the default 60-second derivative cadence and
per-symbol delay protect exchange request limits.

After K-line backfill, replay an individual market into historical features, rule scores, and signals:

```powershell
$env:PYTHONPATH="backend;backend/common;scripts"
python scripts\replay_market_history.py --symbol BTCUSDT --interval 1h --start-time 2026-01-01T00:00:00Z --end-time 2026-04-01T00:00:00Z
```

Set `HISTORICAL_BACKFILL_ENABLED=true` to let the built-in scheduler run a full-market incremental
backfill once per UTC day (defaults to 02:00 UTC and the most recent two days).

With real infrastructure running, validate Redis, ClickHouse, Kafka, gateway health, and a bounded
gateway load sample (this command never uses mocks):

```powershell
python scripts\real_integration_check.py --requests 100 --concurrency 10 --max-p95-ms 500
```

Prometheus evaluates service-down and service-restart alerts from
`deployment/monitoring/alerts.yml`; use `deployment/capacity-baseline.md` as the initial release
capacity checklist.

Run tests:

```powershell
pytest
```

Run the local CI equivalent:

```powershell
python scripts\run_ci.py
```

Validate the Data Platform full MVP contract:

```powershell
python scripts\validate_data_platform_full.py
```

Run smoke checks without external services:

```powershell
$env:PYTHONPATH="backend;backend/common;ai-engine;data-platform"
python scripts/smoke_market_flow.py
python scripts/smoke_apps_import.py
python scripts/smoke_collector_mock.py
python scripts/smoke_market_history_flow.py
python scripts/smoke_history_flow.py
python scripts/smoke_adapters_flow.py
python scripts/smoke_clickhouse_history_flow.py
python scripts/smoke_feature_ranking_flow.py
python scripts/smoke_signal_flow.py
python scripts/smoke_alert_flow.py
python scripts/smoke_screener_flow.py
python scripts/smoke_websocket_flow.py
python scripts/smoke_ai_ranking_signal_flow.py
python scripts/smoke_data_platform_ingest_flow.py
python scripts/smoke_data_platform_kafka_flow.py
python scripts/smoke_notification_flow.py
python scripts/smoke_user_flow.py
```
