import json
from typing import Any, Protocol

from mip_common.clickhouse import (
    ClickHouseClient,
    HttpClickHouseClient,
    datetime_text_to_ms,
    ms_to_datetime_text,
)
from mip_common.config import get_settings

from .schemas import ProcessedEvent, RankingMonitorHistoryEvent, StorageResult


class EventStorage(Protocol):
    async def write(self, processed: ProcessedEvent) -> StorageResult:
        ...

    async def list_ranking_monitor_events(
        self,
        ranking_type: str | None = None,
        exchange: str | None = None,
        symbol: str | None = None,
        event_action: str | None = None,
        limit: int = 100,
    ) -> list[RankingMonitorHistoryEvent]:
        ...


class InMemoryEventStorage:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    async def write(self, processed: ProcessedEvent) -> StorageResult:
        row = self._row(processed)
        if row is not None:
            self.rows.append(row)
        return StorageResult(
            stored=row is not None,
            storage="memory",
            target_table=processed.route.target_table,
            row_count=1 if row is not None else 0,
            reason=None if row is not None else "unsupported_event_type",
        )

    def _row(self, processed: ProcessedEvent) -> dict[str, Any] | None:
        return ClickHouseEventStorage.to_row(processed)

    async def list_ranking_monitor_events(
        self,
        ranking_type: str | None = None,
        exchange: str | None = None,
        symbol: str | None = None,
        event_action: str | None = None,
        limit: int = 100,
    ) -> list[RankingMonitorHistoryEvent]:
        rows = [
            row
            for row in self.rows
            if "ranking_type" in row
            and (ranking_type is None or row["ranking_type"] == ranking_type)
            and (exchange is None or row["exchange"] == exchange.lower())
            and (symbol is None or row["symbol"] == symbol.upper())
            and (event_action is None or row["event_action"] == event_action)
        ]
        rows.sort(key=lambda row: self._timestamp_ms(row["timestamp"]), reverse=True)
        return [ClickHouseEventStorage.history_event_from_row(row) for row in rows[:limit]]

    @staticmethod
    def _timestamp_ms(value: str | int) -> int:
        return value if isinstance(value, int) else datetime_text_to_ms(value)


class ClickHouseEventStorage:
    def __init__(self, client: ClickHouseClient) -> None:
        self.client = client

    async def write(self, processed: ProcessedEvent) -> StorageResult:
        row = self.to_row(processed)
        if row is None:
            return StorageResult(
                stored=False,
                storage="clickhouse",
                target_table=processed.route.target_table,
                row_count=0,
                reason="unsupported_event_type",
            )
        await self.client.insert(processed.route.target_table, [row])
        return StorageResult(
            stored=True,
            storage="clickhouse",
            target_table=processed.route.target_table,
            row_count=1,
        )

    async def list_ranking_monitor_events(
        self,
        ranking_type: str | None = None,
        exchange: str | None = None,
        symbol: str | None = None,
        event_action: str | None = None,
        limit: int = 100,
    ) -> list[RankingMonitorHistoryEvent]:
        rows = await self.client.select(
            "SELECT exchange, symbol, ranking_type, event_action, from_rank, to_rank, "
            "score, previous_score, score_change, market_bias, summary, timestamp "
            "FROM ranking_monitor_event ORDER BY timestamp DESC LIMIT {limit:UInt32}",
            {"limit": max(1, min(limit * 3, 1000))},
        )
        values = [
            self.history_event_from_row(row)
            for row in rows
            if (ranking_type is None or row["ranking_type"] == ranking_type)
            and (exchange is None or row["exchange"] == exchange.lower())
            and (symbol is None or row["symbol"] == symbol.upper())
            and (event_action is None or row["event_action"] == event_action)
        ]
        return values[:limit]

    @staticmethod
    def to_row(processed: ProcessedEvent) -> dict[str, Any] | None:
        data = processed.normalized_data
        timestamp = ms_to_datetime_text(processed.event.timestamp)
        if processed.route.target_table == "event_dead_letter":
            return {
                "event_type": processed.event.event_type,
                "source": processed.event.source,
                "reason": ",".join(issue.code for issue in processed.quality.issues),
                "payload": json.dumps(processed.event.data, separators=(",", ":")),
                "timestamp": timestamp,
            }
        if processed.event.event_type == "market.ticker":
            return {
                "exchange": data.get("exchange", processed.event.source).lower(),
                "symbol": data["symbol"],
                "price": float(data["price"]),
                "change_24h": float(data.get("change24h", data.get("change_24h", 0.0))),
                "volume_24h": float(data.get("volume24h", data.get("volume_24h", 0.0))),
                "timestamp": timestamp,
            }
        if processed.event.event_type == "market.kline":
            return {
                "exchange": data.get("exchange", processed.event.source).lower(),
                "symbol": data["symbol"],
                "interval": data.get("interval", "1m"),
                "open": float(data["open"]),
                "high": float(data["high"]),
                "low": float(data["low"]),
                "close": float(data["close"]),
                "volume": float(data["volume"]),
                "quote_volume": float(data.get("quoteVolume", data.get("quote_volume", 0.0))),
                "timestamp": timestamp,
                "created_at": timestamp,
            }
        if processed.event.event_type == "market.trade":
            return {
                "exchange": data.get("exchange", processed.event.source).lower(),
                "symbol": data["symbol"],
                "trade_id": str(data.get("tradeId", processed.route.dedupe_key)),
                "price": float(data["price"]),
                "quantity": float(data["quantity"]),
                "side": data.get("side", "unknown"),
                "timestamp": timestamp,
            }
        if processed.event.event_type == "market.funding":
            return {
                "exchange": data.get("exchange", processed.event.source).lower(),
                "symbol": data["symbol"],
                "funding_rate": float(data["fundingRate"]),
                "next_funding_time": ms_to_datetime_text(
                    int(data.get("nextFundingTime", processed.event.timestamp))
                ),
                "funding_time": timestamp,
                "source": data.get("source", processed.event.source),
            }
        if processed.event.event_type == "market.open_interest":
            return {
                "exchange": data.get("exchange", processed.event.source).lower(),
                "symbol": data["symbol"],
                "open_interest": float(data["openInterest"]),
                "change_rate": float(data.get("changeRate", 0.0)),
                "timestamp": timestamp,
                "source": data.get("source", processed.event.source),
            }
        if processed.event.event_type == "market.liquidation":
            return {
                "exchange": data.get("exchange", processed.event.source).lower(),
                "symbol": data["symbol"],
                "side": data["side"],
                "price": float(data["price"]),
                "quantity": float(data["quantity"]),
                "value": float(data["value"]),
                "timestamp": timestamp,
                "source": data.get("source", processed.event.source),
            }
        if processed.event.event_type == "feature.updated":
            return {
                "exchange": data.get("exchange", processed.event.source).lower(),
                "symbol": data["symbol"],
                "feature_name": data["feature"],
                "feature_value": float(data["value"]),
                "version": data.get("version", "v1"),
                "timestamp": timestamp,
            }
        if processed.event.event_type == "ranking.updated":
            return {
                "exchange": data.get("exchange", processed.event.source).lower(),
                "symbol": data["symbol"],
                "score_type": data.get("type", "overall"),
                "score": float(data.get("score", data.get("overallScore", 0.0))),
                "timestamp": timestamp,
            }
        if processed.event.event_type in {
            "ranking.entered",
            "ranking.exited",
            "ranking.moved",
            "ranking.strategy",
        }:
            item = data.get("item") or {}
            summary = data.get("summary") or {}
            row = item if isinstance(item, dict) else {}
            exchange = data.get("exchange", row.get("exchange", processed.event.source))
            symbol = data.get("symbol") or row.get("symbol") or data.get("event", "market")
            if processed.event.event_type == "ranking.strategy":
                summary = {
                    **summary,
                    "event": data.get("event"),
                    "severity": data.get("severity"),
                    "title": data.get("title"),
                    "body": data.get("body"),
                }
            return {
                "exchange": exchange.lower(),
                "symbol": symbol,
                "ranking_type": data["rankingType"],
                "event_action": str(
                    data.get("event") or processed.event.event_type.rsplit(".", 1)[-1]
                ),
                "from_rank": int(data.get("fromRank") or row.get("rank") or 0),
                "to_rank": int(data.get("toRank") or row.get("rank") or 0),
                "score": float(data.get("score", row.get("score", 0.0)) or 0.0),
                "previous_score": float(data.get("previousScore", 0.0) or 0.0),
                "score_change": float(data.get("scoreChange", 0.0) or 0.0),
                "market_bias": str(summary.get("marketBias", "")),
                "summary": json.dumps(summary, separators=(",", ":")),
                "timestamp": timestamp,
            }
        if processed.event.event_type == "signal.created":
            return {
                "signal_id": data.get("signalId", processed.route.dedupe_key),
                "exchange": data.get("exchange", processed.event.source).lower(),
                "symbol": data["symbol"],
                "signal_type": data["type"],
                "score": float(data["score"]),
                "confidence": float(data["confidence"]),
                "reason": ",".join(data.get("reasons", [])),
                "timestamp": timestamp,
            }
        return None

    @staticmethod
    def history_event_from_row(row: dict[str, Any]) -> RankingMonitorHistoryEvent:
        summary = row.get("summary") or "{}"
        parsed_summary = json.loads(summary) if isinstance(summary, str) and summary else summary
        return RankingMonitorHistoryEvent(
            exchange=row["exchange"],
            symbol=row["symbol"],
            rankingType=row["ranking_type"],
            eventAction=row["event_action"],
            fromRank=int(row.get("from_rank") or 0),
            toRank=int(row.get("to_rank") or 0),
            score=float(row.get("score") or 0.0),
            previousScore=float(row.get("previous_score") or 0.0),
            scoreChange=float(row.get("score_change") or 0.0),
            marketBias=str(row.get("market_bias") or ""),
            summary=parsed_summary if isinstance(parsed_summary, dict) else {},
            timestamp=(
                int(row["timestamp"])
                if isinstance(row["timestamp"], int)
                else datetime_text_to_ms(row["timestamp"])
            ),
        )


def create_event_storage() -> EventStorage:
    settings = get_settings()
    if settings.data_platform_storage_backend == "clickhouse":
        return ClickHouseEventStorage(
            HttpClickHouseClient(
                base_url=settings.clickhouse_url,
                database=settings.clickhouse_database,
                user=settings.clickhouse_user,
                password=settings.clickhouse_password,
            )
        )
    return InMemoryEventStorage()
