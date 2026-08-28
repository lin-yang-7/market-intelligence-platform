"""Backfill Binance spot klines into ClickHouse.

This task intentionally stores only source market candles.  Derived features,
scores, and signals must be recalculated by their own historical processors.
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parents[1]
for python_root in (ROOT / "backend", ROOT / "backend" / "common"):
    sys.path.insert(0, str(python_root))

from mip_common.clickhouse import (  # noqa: E402
    ClickHouseClient,
    HttpClickHouseClient,
    datetime_text_to_ms,
    ms_to_datetime_text,
)
from mip_common.config import get_settings  # noqa: E402
from mip_common.history import ClickHouseMarketHistoryRepository  # noqa: E402
from services.market_service.app.schemas import KlineResponse  # noqa: E402

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
INTERVAL_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
}


class HttpClient(Protocol):
    async def get(self, url: str, *, params: dict[str, Any]) -> Any:
        ...


def parse_timestamp(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.timestamp() * 1000)


async def existing_timestamps(
    client: ClickHouseClient,
    symbol: str,
    interval: str,
    start_time: int,
    end_time: int,
) -> set[int]:
    rows = await client.select(
        "SELECT timestamp FROM market_kline "
        "WHERE exchange = {exchange:String} AND symbol = {symbol:String} "
        "AND interval = {interval:String} AND timestamp >= {start:DateTime} "
        "AND timestamp <= {end:DateTime}",
        {
            "exchange": "binance",
            "symbol": symbol.upper(),
            "interval": interval,
            "start": ms_to_datetime_text(start_time),
            "end": ms_to_datetime_text(end_time),
        },
    )
    return {datetime_text_to_ms(row["timestamp"]) for row in rows}


def parse_kline(row: list[Any], symbol: str, interval: str) -> KlineResponse:
    return KlineResponse(
        symbol=symbol.upper(),
        exchange="binance",
        interval=interval,
        timestamp=int(row[0]),
        open=float(row[1]),
        high=float(row[2]),
        low=float(row[3]),
        close=float(row[4]),
        volume=float(row[5]),
        quoteVolume=float(row[7]),
        source="binance.rest.klines",
    )


async def backfill_symbol(
    http_client: HttpClient,
    clickhouse_client: ClickHouseClient,
    symbol: str,
    interval: str,
    start_time: int,
    end_time: int,
    request_delay_seconds: float = 0.15,
    max_retries: int = 3,
) -> int:
    if interval not in INTERVAL_MS:
        raise ValueError(f"Unsupported Binance kline interval: {interval}")
    existing = await existing_timestamps(
        clickhouse_client,
        symbol,
        interval,
        start_time,
        end_time,
    )
    repository = ClickHouseMarketHistoryRepository(clickhouse_client)
    cursor = start_time
    inserted = 0
    while cursor <= end_time:
        rows = await fetch_kline_page(
            http_client,
            symbol,
            interval,
            cursor,
            end_time,
            max_retries,
        )
        if not rows:
            break
        klines = [parse_kline(row, symbol, interval) for row in rows]
        await repository.save_klines([kline for kline in klines if kline.timestamp not in existing])
        inserted += sum(kline.timestamp not in existing for kline in klines)
        existing.update(kline.timestamp for kline in klines)
        next_cursor = klines[-1].timestamp + INTERVAL_MS[interval]
        if next_cursor <= cursor:
            raise RuntimeError("Binance kline pagination did not advance")
        cursor = next_cursor
        if request_delay_seconds:
            await asyncio.sleep(request_delay_seconds)
    return inserted


async def fetch_kline_page(
    http_client: HttpClient,
    symbol: str,
    interval: str,
    start_time: int,
    end_time: int,
    max_retries: int,
) -> list[list[Any]]:
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000,
    }
    for attempt in range(max_retries + 1):
        try:
            response = await http_client.get(BINANCE_KLINES_URL, params=params)
            response.raise_for_status()
            return response.json()
        except Exception:
            if attempt >= max_retries:
                raise
            await asyncio.sleep(2**attempt)
    raise RuntimeError("Unreachable")


async def run(args: argparse.Namespace) -> int:
    import httpx

    settings = get_settings()
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    end_time = parse_timestamp(args.end_time) if args.end_time else now_ms
    start_time = (
        parse_timestamp(args.start_time)
        if args.start_time
        else int((datetime.now(UTC) - timedelta(days=args.days)).timestamp() * 1000)
    )
    if start_time >= end_time:
        raise ValueError("start time must be earlier than end time")
    client = HttpClickHouseClient(
        settings.clickhouse_url,
        settings.clickhouse_database,
        settings.clickhouse_user,
        settings.clickhouse_password,
    )
    symbols = [symbol.strip().upper() for symbol in args.symbols.split(",") if symbol.strip()]
    async with httpx.AsyncClient(timeout=20) as http_client:
        for symbol in symbols:
            inserted = await backfill_symbol(
                http_client,
                client,
                symbol,
                args.interval,
                start_time,
                end_time,
                args.request_delay,
                args.max_retries,
            )
            print(f"{symbol} {args.interval}: inserted {inserted} klines")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill Binance spot klines into ClickHouse")
    parser.add_argument("--symbols", default=get_settings().collector_symbols)
    parser.add_argument("--interval", default="1h", choices=sorted(INTERVAL_MS))
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--start-time", help="ISO-8601 UTC time, for example 2026-01-01T00:00:00Z")
    parser.add_argument("--end-time", help="ISO-8601 UTC time; defaults to now")
    parser.add_argument("--request-delay", type=float, default=0.15)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()
    if args.days <= 0:
        parser.error("--days must be positive")
    if args.request_delay < 0 or args.max_retries < 0:
        parser.error("--request-delay and --max-retries cannot be negative")
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
