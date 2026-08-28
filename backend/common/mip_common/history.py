from typing import Any

from .clickhouse import ClickHouseClient, datetime_text_to_ms, ms_to_datetime_text
from .models import validate_model


class ClickHouseMarketHistoryRepository:
    def __init__(self, client: ClickHouseClient) -> None:
        self.client = client

    async def save_klines(self, klines: list[Any]) -> None:
        await self.client.insert(
            "market_kline",
            [
                {
                    "exchange": kline.exchange,
                    "symbol": kline.symbol,
                    "interval": kline.interval,
                    "open": kline.open,
                    "high": kline.high,
                    "low": kline.low,
                    "close": kline.close,
                    "volume": kline.volume,
                    "quote_volume": kline.quoteVolume or 0.0,
                    "timestamp": ms_to_datetime_text(kline.timestamp),
                    "created_at": ms_to_datetime_text(kline.timestamp),
                }
                for kline in klines
            ],
        )

    async def save_trades(self, trades: list[Any]) -> None:
        await self.client.insert(
            "market_trade",
            [
                {
                    "exchange": trade.exchange,
                    "symbol": trade.symbol,
                    "trade_id": trade.tradeId,
                    "price": trade.price,
                    "quantity": trade.quantity,
                    "side": trade.side,
                    "timestamp": ms_to_datetime_text(trade.timestamp),
                }
                for trade in trades
            ],
        )

    async def list_klines(
        self,
        model_class,
        symbol: str,
        interval: str,
        exchange: str | None = None,
        limit: int = 100,
    ) -> list[Any]:
        rows = await self.client.select(
            "SELECT exchange, symbol, interval, open, high, low, close, volume, "
            "quote_volume, timestamp FROM market_kline "
            "WHERE symbol = {symbol:String} AND interval = {interval:String} "
            "ORDER BY timestamp DESC LIMIT {limit:UInt32}",
            {"symbol": symbol.upper(), "interval": interval.lower(), "limit": limit},
        )
        values = [
            validate_model(
                model_class,
                {
                    "exchange": row["exchange"],
                    "symbol": row["symbol"],
                    "interval": row["interval"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                    "quoteVolume": float(row.get("quote_volume") or 0.0),
                    "timestamp": datetime_text_to_ms(row["timestamp"]),
                },
            )
            for row in rows
            if exchange is None or row["exchange"] == exchange.lower()
        ]
        values.sort(key=lambda value: value.timestamp)
        return values


class ClickHouseFeatureHistoryRepository:
    def __init__(self, client: ClickHouseClient) -> None:
        self.client = client

    async def save_features(self, features: list[Any]) -> None:
        await self.client.insert(
            "feature_history",
            [
                {
                    "exchange": feature.exchange,
                    "symbol": feature.symbol,
                    "feature_name": feature.feature,
                    "feature_value": feature.value,
                    "version": feature.version,
                    "timestamp": ms_to_datetime_text(feature.timestamp),
                }
                for feature in features
            ],
        )

    async def list_history(
        self,
        model_class,
        symbol: str,
        feature: str,
        exchange: str | None = None,
        limit: int = 100,
    ) -> list[Any]:
        rows = await self.client.select(
            "SELECT exchange, symbol, feature_name, feature_value, version, timestamp "
            "FROM feature_history WHERE symbol = {symbol:String} "
            "AND feature_name = {feature:String} ORDER BY timestamp DESC LIMIT {limit:UInt32}",
            {"symbol": symbol.upper(), "feature": feature.lower(), "limit": limit},
        )
        return [
            validate_model(
                model_class,
                {
                    "exchange": row.get("exchange", ""),
                    "symbol": row["symbol"],
                    "feature": row["feature_name"],
                    "value": float(row["feature_value"]),
                    "version": row["version"],
                    "timestamp": datetime_text_to_ms(row["timestamp"]),
                },
            )
            for row in rows
            if exchange is None or row.get("exchange") == exchange.lower()
        ]


class ClickHouseSignalHistoryRepository:
    def __init__(self, client: ClickHouseClient) -> None:
        self.client = client

    async def save_signals(self, signals: list[Any]) -> None:
        await self.client.insert(
            "signal_history",
            [
                {
                    "signal_id": signal.signalId,
                    "exchange": signal.exchange,
                    "symbol": signal.symbol,
                    "signal_type": signal.type,
                    "score": signal.score,
                    "confidence": signal.confidence,
                    "reason": ",".join(signal.reasons),
                    "timestamp": ms_to_datetime_text(signal.timestamp),
                }
                for signal in signals
            ],
        )

    async def list_history(
        self,
        model_class,
        symbol: str,
        signal_type: str | None = None,
        limit: int = 100,
    ) -> list[Any]:
        rows = await self.client.select(
            "SELECT signal_id, exchange, symbol, signal_type, score, confidence, "
            "reason, timestamp FROM signal_history WHERE symbol = {symbol:String} "
            "ORDER BY timestamp DESC LIMIT {limit:UInt32}",
            {"symbol": symbol.upper(), "limit": limit},
        )
        return [
            validate_model(
                model_class,
                {
                    "signalId": row["signal_id"],
                    "exchange": row.get("exchange", ""),
                    "symbol": row["symbol"],
                    "type": row["signal_type"],
                    "score": float(row["score"]),
                    "confidence": float(row["confidence"]),
                    "reasons": [reason for reason in row["reason"].split(",") if reason],
                    "factors": {},
                    "explanation": row["reason"],
                    "timestamp": datetime_text_to_ms(row["timestamp"]),
                },
            )
            for row in rows
            if signal_type is None or row["signal_type"] == signal_type
        ]

