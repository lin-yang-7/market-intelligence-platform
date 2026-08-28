import argparse
import asyncio
import os
from dataclasses import dataclass
from typing import Any

import httpx

DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "LINKUSDT",
    "AVAXUSDT",
    "TRXUSDT",
]


@dataclass(frozen=True)
class CoinSignal:
    symbol: str
    price: float
    change_24h: float
    quote_volume: float
    abnormal_score: float
    opportunity_score: float
    risk_score: float


async def fetch_binance_tickers(symbols: list[str] | None) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(base_url="https://api.binance.com", timeout=15) as client:
        response = await client.get("/api/v3/ticker/24hr")
        response.raise_for_status()
        rows = response.json()

    wanted = {symbol.upper() for symbol in symbols} if symbols else None
    return [
        row
        for row in rows
        if row.get("symbol", "").endswith("USDT")
        and (wanted is None or row.get("symbol") in wanted)
    ]


def score_row(row: dict[str, Any]) -> CoinSignal:
    price = float(row["lastPrice"])
    change = float(row["priceChangePercent"])
    quote_volume = float(row["quoteVolume"])
    volume_score = min(100.0, quote_volume / 50_000_000)
    positive_momentum = max(0.0, change)
    negative_momentum = max(0.0, -change)

    abnormal_score = positive_momentum * 12 + volume_score * 0.5
    opportunity_score = positive_momentum * 8 + volume_score * 0.7
    risk_score = negative_momentum * 14 + max(0.0, 30 - volume_score) * 0.8

    return CoinSignal(
        symbol=row["symbol"],
        price=price,
        change_24h=change,
        quote_volume=quote_volume,
        abnormal_score=round(abnormal_score, 2),
        opportunity_score=round(opportunity_score, 2),
        risk_score=round(risk_score, 2),
    )


def render_list(title: str, rows: list[CoinSignal], score_name: str) -> str:
    lines = [
        "",
        title,
        "Rank  Symbol      Price        24h%    Volume(USDT)     Score",
        "----  ----------  -----------  ------  ---------------  -----",
    ]
    for rank, row in enumerate(rows, start=1):
        score = getattr(row, score_name)
        lines.append(
            f"{rank:<4}  "
            f"{row.symbol:<10}  "
            f"{row.price:>11.4f}  "
            f"{row.change_24h:>5.1f}%  "
            f"{row.quote_volume:>15.0f}  "
            f"{score:>5.1f}"
        )
    return "\n".join(lines)


def build_report(rows: list[CoinSignal], limit: int) -> str:
    abnormal = sorted(rows, key=lambda row: row.abnormal_score, reverse=True)[:limit]
    opportunity = sorted(rows, key=lambda row: row.opportunity_score, reverse=True)[:limit]
    risk = sorted(rows, key=lambda row: row.risk_score, reverse=True)[:limit]
    parts = [
        "简化版智能选币推送",
        render_list("异动看涨榜", abnormal, "abnormal_score"),
        render_list("机会看涨榜", opportunity, "opportunity_score"),
        render_list("风险看跌榜", risk, "risk_score"),
    ]
    return "\n".join(parts)


async def push_report(report: str, webhook_url: str | None) -> None:
    print(report)
    if not webhook_url:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(webhook_url, json={"text": report})
        response.raise_for_status()


async def run_once(symbols: list[str] | None, limit: int, webhook_url: str | None) -> None:
    tickers = await fetch_binance_tickers(symbols)
    rows = [score_row(row) for row in tickers]
    report = build_report(rows, limit)
    await push_report(report, webhook_url)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Simple smart coin monitor.")
    parser.add_argument("symbols", nargs="*", help="Symbols to scan, for example BTCUSDT ETHUSDT.")
    parser.add_argument("--all-usdt", action="store_true", help="Scan all Binance USDT spot pairs.")
    parser.add_argument("--limit", type=int, default=5, help="Rows per list.")
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Repeat interval in seconds. 0 means once.",
    )
    parser.add_argument(
        "--webhook-url",
        default=os.getenv("SMART_COIN_WEBHOOK_URL"),
        help="Optional webhook URL. Defaults to SMART_COIN_WEBHOOK_URL.",
    )
    args = parser.parse_args()

    symbols = (
        None
        if args.all_usdt
        else [symbol.upper() for symbol in args.symbols] or DEFAULT_SYMBOLS
    )
    while True:
        await run_once(symbols, max(1, args.limit), args.webhook_url)
        if args.interval <= 0:
            break
        await asyncio.sleep(args.interval)


if __name__ == "__main__":
    asyncio.run(main())
