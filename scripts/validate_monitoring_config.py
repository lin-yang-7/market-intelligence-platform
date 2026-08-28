import argparse
import json
from pathlib import Path

REQUIRED_PROMETHEUS_TARGETS = {
    "api-gateway:8000",
    "market-service:8001",
    "feature-service:8003",
    "ranking-service:8004",
    "websocket-service:8008",
    "history-service:8009",
    "ai-engine:8010",
    "data-platform:8011",
}


def inspect_monitoring(root: Path) -> dict[str, object]:
    prometheus = root / "deployment/monitoring/prometheus.yml"
    alerts = root / "deployment/monitoring/alerts.yml"
    dashboard = root / "deployment/monitoring/grafana/dashboards/mip-overview.json"
    datasource = root / "deployment/monitoring/grafana/provisioning/datasources/prometheus.yml"
    dashboards = root / "deployment/monitoring/grafana/provisioning/dashboards/dashboards.yml"
    prometheus_text = prometheus.read_text(encoding="utf-8") if prometheus.exists() else ""
    dashboard_payload = (
        json.loads(dashboard.read_text(encoding="utf-8"))
        if dashboard.exists()
        else {}
    )
    return {
        "files": {
            "prometheus": prometheus.exists(),
            "alerts": alerts.exists(),
            "dashboard": dashboard.exists(),
            "datasource": datasource.exists(),
            "dashboard_provider": dashboards.exists(),
        },
        "targets": {
            target
            for target in REQUIRED_PROMETHEUS_TARGETS
            if target in prometheus_text
        },
        "dashboard_title": dashboard_payload.get("title"),
        "dashboard_panels": len(dashboard_payload.get("panels", [])),
        "alerts_text": alerts.read_text(encoding="utf-8") if alerts.exists() else "",
    }


def validate(root: Path) -> list[str]:
    report = inspect_monitoring(root)
    issues = []
    missing_files = [name for name, exists in report["files"].items() if not exists]
    missing_targets = REQUIRED_PROMETHEUS_TARGETS - report["targets"]
    if missing_files:
        issues.append(f"missing monitoring files: {', '.join(sorted(missing_files))}")
    if missing_targets:
        issues.append(f"missing prometheus targets: {', '.join(sorted(missing_targets))}")
    if report["dashboard_title"] != "Market Intelligence Overview":
        issues.append("missing Grafana overview dashboard")
    if report["dashboard_panels"] < 2:
        issues.append("Grafana dashboard must include at least two panels")
    for alert_name in ("MarketIntelligenceServiceDown", "MarketIntelligenceServiceRestarted"):
        if alert_name not in report["alerts_text"]:
            issues.append(f"missing monitoring alert: {alert_name}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate monitoring MVP configuration.")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    issues = validate(Path(args.root).resolve())
    if issues:
        for issue in issues:
            print(f"failed: {issue}")
        return 1
    print("ok: monitoring config includes Prometheus targets and Grafana dashboard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
