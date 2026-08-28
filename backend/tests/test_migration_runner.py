from pathlib import Path

import pytest

from scripts.migration_runner import (
    DryRunAdapter,
    Migration,
    apply_migrations,
    discover_migrations,
    format_plan,
    parse_migration_name,
    pending_migrations,
)


class RecordingAdapter:
    def __init__(self, applied: dict[str, set[str]] | None = None) -> None:
        self._applied = applied or {}
        self.applied: list[tuple[str, str]] = []

    def applied_versions(self, database: str) -> set[str]:
        return self._applied.get(database, set())

    def apply(self, database: str, migration: Migration) -> None:
        self.applied.append((database, migration.version))


def test_discover_migrations_reads_sql_directories(tmp_path: Path) -> None:
    mysql = tmp_path / "mysql"
    clickhouse = tmp_path / "clickhouse"
    mysql.mkdir()
    clickhouse.mkdir()
    (mysql / "001_business_baseline.sql").write_text("CREATE TABLE users;", encoding="utf-8")
    (clickhouse / "001_market_baseline.sql").write_text("CREATE DATABASE x;", encoding="utf-8")

    migrations = discover_migrations(tmp_path)

    assert [(item.database, item.version, item.name) for item in migrations] == [
        ("clickhouse", "001", "market_baseline"),
        ("mysql", "001", "business_baseline"),
    ]
    assert migrations[0].sql == "CREATE DATABASE x;"


def test_parse_migration_name_rejects_invalid_filename() -> None:
    with pytest.raises(ValueError):
        parse_migration_name(Path("baseline.sql"))


def test_pending_and_apply_migrations_skip_applied_versions() -> None:
    migrations = [
        Migration("mysql", "001", "baseline", Path("001_baseline.sql"), "sql-1"),
        Migration("mysql", "002", "users", Path("002_users.sql"), "sql-2"),
        Migration("clickhouse", "001", "market", Path("001_market.sql"), "sql-3"),
    ]
    adapter = RecordingAdapter({"mysql": {"001"}})

    pending = pending_migrations(adapter, migrations)
    applied = apply_migrations(adapter, migrations)

    assert [(item.database, item.version) for item in pending] == [
        ("mysql", "002"),
        ("clickhouse", "001"),
    ]
    assert [(item.database, item.version) for item in applied] == adapter.applied


def test_dry_run_adapter_and_format_plan() -> None:
    migration = Migration("mysql", "001", "baseline", Path("001_baseline.sql"), "sql")
    adapter = DryRunAdapter()

    applied = apply_migrations(adapter, [migration], dry_run=True)

    assert applied == [migration]
    assert adapter.applied == []
    assert "mysql:001 baseline" in format_plan(applied)
    assert format_plan([]) == "No pending migrations."
