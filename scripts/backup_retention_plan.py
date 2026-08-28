from dataclasses import dataclass


@dataclass(frozen=True)
class RetentionPolicy:
    dataset: str
    hot_days: int
    cold_days: int
    delete_after_days: int


POLICIES = [
    RetentionPolicy("market_ticker", hot_days=30, cold_days=365, delete_after_days=1095),
    RetentionPolicy("market_kline", hot_days=90, cold_days=730, delete_after_days=1825),
    RetentionPolicy("feature_history", hot_days=90, cold_days=730, delete_after_days=1825),
    RetentionPolicy("signal_history", hot_days=180, cold_days=1095, delete_after_days=2555),
    RetentionPolicy("prediction_history", hot_days=180, cold_days=1095, delete_after_days=2555),
    RetentionPolicy("notification_deliveries", hot_days=30, cold_days=365, delete_after_days=730),
]


def backup_targets() -> list[str]:
    return [
        "mysql:users",
        "mysql:api_keys",
        "mysql:subscriptions",
        "mysql:usage_counters",
        "mysql:invoices",
        "mysql:payment_events",
        "clickhouse:market_ticker",
        "clickhouse:market_kline",
        "clickhouse:feature_history",
        "clickhouse:signal_history",
        "clickhouse:prediction_history",
        "clickhouse:ranking_history",
    ]


def render_plan() -> str:
    lines = [
        "# Backup And Retention Plan",
        "",
        "## Backup Targets",
        "",
    ]
    lines.extend(f"- {target}" for target in backup_targets())
    lines.extend(["", "## Retention Policies", ""])
    lines.extend(
        "- "
        f"{policy.dataset}: hot={policy.hot_days}d, "
        f"cold={policy.cold_days}d, delete_after={policy.delete_after_days}d"
        for policy in POLICIES
    )
    lines.extend(
        [
            "",
            "## Execution Notes",
            "",
            "- This MVP plan is declarative and does not delete data.",
            "- Production execution should use database-native backup tooling.",
            "- Destructive retention jobs must run with audited dry-run output first.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    print(render_plan())


if __name__ == "__main__":
    main()
