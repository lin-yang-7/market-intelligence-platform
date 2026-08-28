"""Run the full-market backfill once per UTC day when explicitly enabled."""

import asyncio
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
for python_root in (ROOT, ROOT / "backend", ROOT / "backend" / "common"):
    sys.path.insert(0, str(python_root))

from mip_common.config import get_settings  # noqa: E402

from scripts.backfill_binance_market import run as backfill_market  # noqa: E402

logger = logging.getLogger("market-backfill-scheduler")


def should_run(now: datetime, hour_utc: int, last_run_date: str | None) -> bool:
    return now.hour == hour_utc and now.date().isoformat() != last_run_date


def backfill_args(settings, now: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        interval=settings.historical_backfill_interval,
        days=settings.historical_backfill_days,
        start_time=None,
        end_time=None,
        max_symbols=0,
        request_delay=0.15,
        max_retries=3,
        state_file=str(ROOT / "data" / "backfill" / f"binance-usdt-{now.date().isoformat()}.json"),
    )


async def run_forever() -> None:
    last_run_date: str | None = None
    while True:
        settings = get_settings()
        now = datetime.now(UTC)
        if settings.historical_backfill_enabled and should_run(
            now,
            settings.historical_backfill_hour_utc,
            last_run_date,
        ):
            try:
                await backfill_market(backfill_args(settings, now))
                last_run_date = now.date().isoformat()
                logger.info("full-market historical backfill completed")
            except Exception:
                logger.exception("full-market historical backfill failed")
        await asyncio.sleep(max(10, settings.historical_backfill_poll_seconds))


if __name__ == "__main__":
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(run_forever())
