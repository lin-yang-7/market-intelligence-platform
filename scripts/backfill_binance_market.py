"""Discover and resumably backfill the active Binance USDT spot market."""

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any, Protocol

import httpx
from mip_common.clickhouse import HttpClickHouseClient
from mip_common.config import get_settings

try:
    from scripts.backfill_binance_klines import backfill_symbol, parse_timestamp
except ModuleNotFoundError:  # Direct execution keeps scripts/ at the import root.
    from backfill_binance_klines import backfill_symbol, parse_timestamp

BINANCE_EXCHANGE_INFO_URL = "https://api.binance.com/api/v3/exchangeInfo"
BINANCE_24H_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
DEFAULT_STATE_FILE = Path("data/backfill/binance-usdt-state.json")


class HttpClient(Protocol):
    async def get(self, url: str, *, params: dict[str, Any] | None = None) -> Any:
        ...


async def discover_active_usdt_symbols(http_client: HttpClient) -> list[str]:
    exchange_info = await http_client.get(BINANCE_EXCHANGE_INFO_URL)
    exchange_info.raise_for_status()
    ticker_response = await http_client.get(BINANCE_24H_TICKER_URL)
    ticker_response.raise_for_status()
    volumes = {
        str(row["symbol"]): float(row.get("quoteVolume") or 0)
        for row in ticker_response.json()
    }
    symbols = [
        str(row["symbol"])
        for row in exchange_info.json()["symbols"]
        if row.get("status") == "TRADING"
        and row.get("quoteAsset") == "USDT"
        and row.get("isSpotTradingAllowed", True)
        and str(row["symbol"]) in volumes
    ]
    return sorted(symbols, key=lambda symbol: volumes[symbol], reverse=True)


def load_completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(symbol) for symbol in payload.get("completed", [])}


def save_completed(path: Path, completed: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"completed": sorted(completed)}, indent=2) + "\n",
        encoding="utf-8",
    )


async def run(args: argparse.Namespace) -> int:
    settings = get_settings()
    now_ms = int(time.time() * 1000)
    end_time = parse_timestamp(args.end_time) if args.end_time else now_ms
    start_time = (
        parse_timestamp(args.start_time)
        if args.start_time
        else end_time - args.days * 86_400_000
    )
    if start_time >= end_time:
        raise ValueError("start time must be earlier than end time")
    state_file = Path(args.state_file)
    completed = load_completed(state_file)
    clickhouse_client = HttpClickHouseClient(
        settings.clickhouse_url,
        settings.clickhouse_database,
        settings.clickhouse_user,
        settings.clickhouse_password,
    )
    async with httpx.AsyncClient(timeout=30) as http_client:
        symbols = await discover_active_usdt_symbols(http_client)
        if args.max_symbols:
            symbols = symbols[: args.max_symbols]
        for index, symbol in enumerate(symbols, start=1):
            if symbol in completed:
                print(f"[{index}/{len(symbols)}] {symbol}: already completed")
                continue
            inserted = await backfill_symbol(
                http_client,
                clickhouse_client,
                symbol,
                args.interval,
                start_time,
                end_time,
                args.request_delay,
                args.max_retries,
            )
            completed.add(symbol)
            save_completed(state_file, completed)
            print(f"[{index}/{len(symbols)}] {symbol}: inserted {inserted} klines")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill all active Binance USDT spot symbols")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--start-time")
    parser.add_argument("--end-time")
    parser.add_argument("--max-symbols", type=int, default=0, help="0 means every active symbol")
    parser.add_argument("--request-delay", type=float, default=0.15)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE))
    args = parser.parse_args()
    if args.days <= 0 or args.max_symbols < 0 or args.request_delay < 0 or args.max_retries < 0:
        parser.error("numeric options must be non-negative; --days must be positive")
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
