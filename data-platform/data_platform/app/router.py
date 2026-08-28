from .schemas import PipelineEvent, RoutePlan

TABLE_BY_EVENT_TYPE = {
    "market.ticker": "market_ticker",
    "market.kline": "market_kline",
    "market.trade": "market_trade",
    "market.funding": "funding_rate_history",
    "market.open_interest": "open_interest_history",
    "market.liquidation": "liquidation_history",
    "feature.updated": "feature_history",
    "ranking.updated": "score_history",
    "ranking.entered": "ranking_monitor_event",
    "ranking.exited": "ranking_monitor_event",
    "ranking.moved": "ranking_monitor_event",
    "ranking.strategy": "ranking_monitor_event",
    "signal.created": "signal_history",
    "alert.triggered": "alert_history",
}


class ClickHouseRoutePlanner:
    def plan(self, event: PipelineEvent) -> RoutePlan:
        target_table = TABLE_BY_EVENT_TYPE.get(event.event_type, "event_dead_letter")
        symbol = str(event.data.get("symbol", "unknown"))
        return RoutePlan(
            event_type=event.event_type,
            target_table=target_table,
            storage="clickhouse" if target_table != "event_dead_letter" else "dead_letter",
            partition_key=self._partition_key(event.timestamp),
            dedupe_key=f"{event.event_type}:{symbol}:{event.timestamp}",
        )

    def _partition_key(self, timestamp: int) -> str:
        return str(timestamp // 86_400_000)

    def dead_letter(self, event: PipelineEvent, reason: str) -> RoutePlan:
        source = str(event.data.get("symbol", event.source))
        return RoutePlan(
            event_type=event.event_type,
            target_table="event_dead_letter",
            storage="dead_letter",
            partition_key=self._partition_key(event.timestamp),
            dedupe_key=f"dead_letter:{event.event_type}:{source}:{event.timestamp}:{reason}",
        )
