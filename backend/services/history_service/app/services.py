from typing import Any

from .schemas import (
    HistoryQuery,
    HistorySeries,
    HistorySnapshot,
    RankingMonitorHistoryEvent,
    TimelineEvent,
)
from .sources import HistorySource

DEFAULT_FEATURES = ["long_inflow_score", "volume_spike_score", "momentum_score"]


class HistoryService:
    def __init__(
        self,
        source: HistorySource,
        market_service_url: str,
        feature_service_url: str,
        signal_service_url: str,
        data_platform_url: str = "http://localhost:8011",
    ) -> None:
        self.source = source
        self.market_service_url = market_service_url
        self.feature_service_url = feature_service_url
        self.signal_service_url = signal_service_url
        self.data_platform_url = data_platform_url

    async def snapshot(self, query: HistoryQuery) -> HistorySnapshot:
        klines = await self._klines(query)
        feature_series = await self._features(query)
        signals = await self._signals(query)
        series = [
            HistorySeries(name="price", type="kline", points=klines),
            *feature_series,
            HistorySeries(name="signals", type="signal", points=signals),
        ]
        timeline = self._timeline(query.symbol, klines, feature_series, signals)
        return HistorySnapshot(
            symbol=query.symbol.upper(),
            exchange=query.exchange.lower() if query.exchange else None,
            interval=query.interval,
            series=series,
            timeline=timeline,
        )

    async def timeline(self, query: HistoryQuery) -> list[TimelineEvent]:
        snapshot = await self.snapshot(query)
        return snapshot.timeline

    async def ranking_monitor_events(
        self,
        ranking_type: str | None = None,
        exchange: str | None = None,
        symbol: str | None = None,
        event_action: str | None = None,
        limit: int = 100,
    ) -> list[RankingMonitorHistoryEvent]:
        params: dict[str, Any] = {"limit": limit}
        if ranking_type:
            params["rankingType"] = ranking_type
        if exchange:
            params["exchange"] = exchange
        if symbol:
            params["symbol"] = symbol
        if event_action:
            params["eventAction"] = event_action
        rows = await self.source.get(
            self.data_platform_url,
            "/v1/data/ranking-monitor/events",
            params,
        )
        return [RankingMonitorHistoryEvent(**row) for row in rows]

    async def _klines(self, query: HistoryQuery) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "symbol": query.symbol,
            "interval": query.interval,
            "limit": query.limit,
        }
        if query.exchange:
            params["exchange"] = query.exchange
        return await self.source.get(self.market_service_url, "/v1/market/kline", params)

    async def _features(self, query: HistoryQuery) -> list[HistorySeries]:
        features = query.features or DEFAULT_FEATURES
        series: list[HistorySeries] = []
        for feature in features:
            params: dict[str, Any] = {
                "symbol": query.symbol,
                "feature": feature,
                "limit": query.limit,
            }
            if query.exchange:
                params["exchange"] = query.exchange
            if query.startTime is not None:
                params["startTime"] = query.startTime
            if query.endTime is not None:
                params["endTime"] = query.endTime
            points = await self.source.get(self.feature_service_url, "/v1/feature/history", params)
            series.append(HistorySeries(name=feature, type="feature", points=points))
        return series

    async def _signals(self, query: HistoryQuery) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"symbol": query.symbol, "limit": query.limit}
        if query.signalType:
            params["type"] = query.signalType
        if query.startTime is not None:
            params["startTime"] = query.startTime
        if query.endTime is not None:
            params["endTime"] = query.endTime
        return await self.source.get(self.signal_service_url, "/v1/signal/history", params)

    def _timeline(
        self,
        symbol: str,
        klines: list[dict[str, Any]],
        feature_series: list[HistorySeries],
        signals: list[dict[str, Any]],
    ) -> list[TimelineEvent]:
        events = [
            TimelineEvent(
                timestamp=signal["timestamp"],
                source="signal",
                symbol=signal.get("symbol", symbol).upper(),
                type=signal.get("type", "signal"),
                title=f"{signal.get('type', 'signal')} score {signal.get('score', 0)}",
                payload=signal,
            )
            for signal in signals
        ]
        for series in feature_series:
            for point in series.points:
                if float(point.get("value", 0)) >= 80:
                    events.append(
                        TimelineEvent(
                            timestamp=point["timestamp"],
                            source="feature",
                            symbol=point.get("symbol", symbol).upper(),
                            type=series.name,
                            title=f"{series.name} reached {point.get('value')}",
                            payload=point,
                        )
                    )
        if klines:
            last = klines[-1]
            events.append(
                TimelineEvent(
                    timestamp=last["timestamp"],
                    source="market",
                    symbol=last.get("symbol", symbol).upper(),
                    type="price",
                    title=f"close {last.get('close')}",
                    payload=last,
                )
            )
        events.sort(key=lambda event: event.timestamp, reverse=True)
        return events
