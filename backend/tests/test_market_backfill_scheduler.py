from datetime import UTC, datetime
from types import SimpleNamespace

from scripts.market_backfill_scheduler import backfill_args, should_run


def test_scheduler_runs_once_at_configured_utc_hour() -> None:
    now = datetime(2026, 8, 28, 2, 30, tzinfo=UTC)

    assert should_run(now, 2, None)
    assert not should_run(now, 2, "2026-08-28")
    assert not should_run(now, 3, None)


def test_scheduler_uses_daily_checkpoint() -> None:
    settings = SimpleNamespace(
        historical_backfill_interval="1h",
        historical_backfill_days=2,
    )
    args = backfill_args(settings, datetime(2026, 8, 28, tzinfo=UTC))

    assert args.max_symbols == 0
    assert args.state_file.endswith("binance-usdt-2026-08-28.json")
