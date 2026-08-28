import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parents[1]
SQL_ROOT = ROOT / "sql"


class MigrationAdapter(Protocol):
    def applied_versions(self, database: str) -> set[str]:
        ...

    def apply(self, database: str, migration: "Migration") -> None:
        ...


@dataclass(frozen=True)
class Migration:
    database: str
    version: str
    name: str
    path: Path
    sql: str


class DryRunAdapter:
    def __init__(self) -> None:
        self.applied: list[Migration] = []

    def applied_versions(self, database: str) -> set[str]:
        return set()

    def apply(self, database: str, migration: Migration) -> None:
        self.applied.append(migration)


def discover_migrations(sql_root: Path = SQL_ROOT) -> list[Migration]:
    migrations: list[Migration] = []
    for database_dir in sorted(path for path in sql_root.iterdir() if path.is_dir()):
        for path in sorted(database_dir.glob("*.sql")):
            version, name = parse_migration_name(path)
            migrations.append(
                Migration(
                    database=database_dir.name,
                    version=version,
                    name=name,
                    path=path,
                    sql=path.read_text(encoding="utf-8"),
                )
            )
    return migrations


def parse_migration_name(path: Path) -> tuple[str, str]:
    stem = path.stem
    version, _, name = stem.partition("_")
    if not version.isdigit() or not name:
        raise ValueError(f"Invalid migration filename: {path.name}")
    return version, name


def pending_migrations(adapter: MigrationAdapter, migrations: list[Migration]) -> list[Migration]:
    pending: list[Migration] = []
    applied_by_db: dict[str, set[str]] = {}
    for migration in migrations:
        applied = applied_by_db.setdefault(
            migration.database,
            adapter.applied_versions(migration.database),
        )
        if migration.version not in applied:
            pending.append(migration)
    return pending


def apply_migrations(
    adapter: MigrationAdapter,
    migrations: list[Migration],
    dry_run: bool = False,
) -> list[Migration]:
    pending = pending_migrations(adapter, migrations)
    if dry_run:
        return pending
    for migration in pending:
        adapter.apply(migration.database, migration)
    return pending


def format_plan(migrations: list[Migration]) -> str:
    if not migrations:
        return "No pending migrations."
    lines = ["Pending migrations:"]
    lines.extend(
        f"- {migration.database}:{migration.version} {migration.name} ({migration.path})"
        for migration in migrations
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Market Intelligence migration runner")
    parser.add_argument("command", choices=["plan", "apply"])
    parser.add_argument("--dry-run", action="store_true", help="Do not execute migrations")
    args = parser.parse_args()

    adapter = DryRunAdapter()
    migrations = discover_migrations()
    if args.command == "plan" or args.dry_run:
        print(format_plan(pending_migrations(adapter, migrations)))
        return
    applied = apply_migrations(adapter, migrations)
    print(format_plan(applied))


if __name__ == "__main__":
    main()
