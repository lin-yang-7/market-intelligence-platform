import argparse
from pathlib import Path

REQUIRED_ARTIFACTS = {
    "docker_compose": "deployment/docker-compose.yml",
    "mysql_schema": "sql/mysql/001_business_baseline.sql",
    "clickhouse_schema": "sql/clickhouse/001_market_baseline.sql",
    "backup_plan": "docs/generated/BACKUP-RETENTION-PLAN.md",
    "deployment_runbook": "docs/generated/PRODUCTION-DEPLOYMENT-RUNBOOK.md",
    "health_check": "scripts/check_deployment_health.py",
}

RECOVERY_CHECKS = [
    "Freeze writes or route traffic to maintenance mode before database restore.",
    "Restore MySQL baseline and latest user/configuration backup.",
    "Restore ClickHouse baseline and latest historical analytics backup.",
    "Restore Redis AOF/RDB only when session or real-time state recovery is required.",
    "Start infrastructure services before application services.",
    "Run deployment health check after restore.",
    "Verify ranking monitor historical event query after restore.",
]


def inspect_artifacts(root: Path) -> dict[str, bool]:
    return {
        name: (root / relative_path).exists()
        for name, relative_path in REQUIRED_ARTIFACTS.items()
    }


def render_report(root: Path) -> str:
    artifacts = inspect_artifacts(root)
    lines = [
        "# Disaster Recovery Readiness Check",
        "",
        "## Required Artifacts",
        "",
    ]
    for name, exists in artifacts.items():
        marker = "ok" if exists else "missing"
        lines.append(f"- {name}: {marker} ({REQUIRED_ARTIFACTS[name]})")
    lines.extend(["", "## Recovery Checks", ""])
    lines.extend(f"- {item}" for item in RECOVERY_CHECKS)
    lines.extend(
        [
            "",
            "## Status",
            "",
            "ready" if all(artifacts.values()) else "not_ready",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check disaster recovery readiness artifacts.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--output", default="", help="Optional report output path.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = render_report(root)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0 if all(inspect_artifacts(root).values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
