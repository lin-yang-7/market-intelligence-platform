"""Replay stored K-lines into feature, score, and signal history."""

import argparse
import asyncio
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for python_root in (ROOT / "backend", ROOT / "backend" / "common"):
    sys.path.insert(0, str(python_root))

from mip_common.clickhouse import (  # noqa: E402
    HttpClickHouseClient,
    datetime_text_to_ms,
    ms_to_datetime_text,
)
from mip_common.config import get_settings  # noqa: E402
from mip_common.events import MarketEvent  # noqa: E402
from mip_common.history import (  # noqa: E402
    ClickHouseFeatureHistoryRepository,
    ClickHouseSignalHistoryRepository,
)
from services.feature_service.app.repositories import InMemoryFeatureRepository  # noqa: E402
from services.feature_service.app.schemas import FeatureValue  # noqa: E402
from services.feature_service.app.services import FeatureService  # noqa: E402
from services.ranking_service.app.schemas import RankingItem  # noqa: E402
from services.score_service.app.schemas import ScoreRequest  # noqa: E402
from services.score_service.app.services import ScoreService  # noqa: E402
from services.signal_service.app.repositories import InMemorySignalRepository  # noqa: E402
from services.signal_service.app.services import SignalService  # noqa: E402


async def load_klines(
    client: HttpClickHouseClient,
    symbol: str,
    interval: str,
    start_time: int,
    end_time: int,
) -> list[dict]:
    return await client.select(
        "SELECT exchange, symbol, interval, open, high, low, close, volume, quote_volume, "
        "timestamp "
        "FROM market_kline WHERE exchange = {exchange:String} AND symbol = {symbol:String} "
        "AND interval = {interval:String} AND timestamp >= {start:DateTime} "
        "AND timestamp <= {end:DateTime} ORDER BY timestamp ASC",
        {
            "exchange": "binance",
            "symbol": symbol.upper(),
            "interval": interval,
            "start": ms_to_datetime_text(start_time),
            "end": ms_to_datetime_text(end_time),
        },
    )


def replay_window_size(interval: str) -> int:
    units = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "12h": 720,
        "1d": 1440,
    }
    if interval not in units or 1440 % units[interval] != 0:
        raise ValueError("interval must divide one day and be supported by the replay processor")
    return 1440 // units[interval]


async def replay_rows(rows: list[dict]) -> tuple[list[FeatureValue], list[dict], list]:
    if not rows:
        return [], [], []
    interval = str(rows[0]["interval"])
    window = replay_window_size(interval)
    features = FeatureService(InMemoryFeatureRepository())
    scores = ScoreService()
    signals = SignalService(InMemorySignalRepository())
    closes: deque[float] = deque(maxlen=window + 1)
    volumes: deque[float] = deque(maxlen=window)
    feature_history: list[FeatureValue] = []
    score_history: list[dict] = []
    signal_history: list = []
    for row in rows:
        close = float(row["close"])
        quote_volume = float(row.get("quote_volume") or row.get("volume") or 0.0)
        closes.append(close)
        volumes.append(quote_volume)
        baseline = closes[0]
        change_24h = ((close - baseline) / baseline * 100) if baseline else 0.0
        event = MarketEvent(
            event="market.ticker",
            exchange=str(row["exchange"]).lower(),
            timestamp=datetime_text_to_ms(row["timestamp"]),
            data={
                "symbol": str(row["symbol"]).upper(),
                "price": close,
                "change24h": change_24h,
                "volume24h": sum(volumes),
                "source": "history-replay",
            },
        )
        current_features = await features.calculate_from_market_event(event)
        feature_history.extend(current_features)
        factors = {value.feature: value.value for value in current_features}
        result = await scores.calculate(
            ScoreRequest(symbol=event.data["symbol"], exchange=event.exchange, factors=factors)
        )
        score_history.append(
            {
                "exchange": event.exchange,
                "symbol": event.data["symbol"],
                "score_type": result.scoreType,
                "score": result.score,
                "confidence": result.confidence,
                "model_version": result.modelVersion or "rule-v1",
                "opportunity_score": result.opportunityScore or 0.0,
                "risk_score": result.riskScore or 0.0,
                "timestamp": ms_to_datetime_text(event.timestamp),
            }
        )
        item = RankingItem(
            rank=1,
            symbol=event.data["symbol"],
            exchange=event.exchange,
            score=result.score,
            confidence=result.confidence,
            timestamp=event.timestamp,
            factors=result.factors,
            modelVersion=result.modelVersion,
        )
        signal_history.extend(await signals.generate_from_ranking("overall", [item]))
    return feature_history, score_history, signal_history


async def run(args: argparse.Namespace) -> int:
    from scripts.backfill_binance_klines import parse_timestamp

    settings = get_settings()
    client = HttpClickHouseClient(
        settings.clickhouse_url,
        settings.clickhouse_database,
        settings.clickhouse_user,
        settings.clickhouse_password,
    )
    rows = await load_klines(
        client,
        args.symbol,
        args.interval,
        parse_timestamp(args.start_time),
        parse_timestamp(args.end_time),
    )
    feature_values, score_rows, signals = await replay_rows(rows)
    await ClickHouseFeatureHistoryRepository(client).save_features(feature_values)
    await client.insert("score_history", score_rows)
    await ClickHouseSignalHistoryRepository(client).save_signals(signals)
    print(
        f"replayed {len(rows)} klines, {len(feature_values)} features, "
        f"{len(score_rows)} scores, {len(signals)} signals"
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay K-lines into historical features, scores, and signals"
    )
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--start-time", required=True)
    parser.add_argument("--end-time", required=True)
    raise SystemExit(asyncio.run(run(parser.parse_args())))


if __name__ == "__main__":
    main()
