# Monitoring MVP Runbook

## Scope

This runbook covers the current Prometheus and Grafana MVP configuration.
Services already expose Prometheus-format metrics on `/metrics`.

## Files

- `deployment/monitoring/prometheus.yml`
- `deployment/monitoring/grafana/provisioning/datasources/prometheus.yml`
- `deployment/monitoring/grafana/provisioning/dashboards/dashboards.yml`
- `deployment/monitoring/grafana/dashboards/mip-overview.json`

## Docker Compose

Start the stack:

```powershell
docker compose -f deployment/docker-compose.yml up -d --build
```

Open:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

Default Grafana credentials are controlled by:

- `GRAFANA_ADMIN_USER`
- `GRAFANA_ADMIN_PASSWORD`

If unset, both default to `admin` for internal MVP use.

## Validate

```powershell
python scripts\validate_monitoring_config.py
```

## MVP Dashboard

Dashboard:

- `Market Intelligence Overview`

Panels:

- `Service Up`
- `Service Uptime`

## Remaining Work

- Request latency histogram metrics.
- Error-rate metrics.
- Kafka lag exporter.
- Database exporters.
- Alertmanager rules.
