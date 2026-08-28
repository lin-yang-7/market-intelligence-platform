from mip_common.responses import now_ms

from .schemas import WebSocketEvent


def sample_event(channel: str) -> WebSocketEvent:
    timestamp = now_ms()
    if channel == "market.ticker":
        return WebSocketEvent(
            event=channel,
            timestamp=timestamp,
            data={"symbol": "BTCUSDT", "price": 68000, "timestamp": timestamp},
        )
    if channel == "ranking.updated":
        return WebSocketEvent(
            event=channel,
            timestamp=timestamp,
            data={"type": "longInflow", "symbol": "BTCUSDT", "rank": 1, "score": 95},
        )
    if channel == "ranking.monitor.updated":
        return WebSocketEvent(
            event=channel,
            timestamp=timestamp,
            data={
                "rankingType": "opportunityBullish",
                "active": [],
                "changes": {"entered": [], "exited": [], "moved": []},
            },
        )
    if channel == "ranking.entered":
        return WebSocketEvent(
            event=channel,
            timestamp=timestamp,
            data={"rankingType": "opportunityBullish", "symbol": "BTCUSDT", "toRank": 1},
        )
    if channel == "ranking.exited":
        return WebSocketEvent(
            event=channel,
            timestamp=timestamp,
            data={"rankingType": "opportunityBullish", "symbol": "ETHUSDT", "fromRank": 2},
        )
    if channel == "ranking.moved":
        return WebSocketEvent(
            event=channel,
            timestamp=timestamp,
            data={
                "rankingType": "opportunityBullish",
                "symbol": "SOLUSDT",
                "fromRank": 3,
                "toRank": 2,
            },
        )
    if channel == "ranking.strategy":
        return WebSocketEvent(
            event=channel,
            timestamp=timestamp,
            data={
                "rankingType": "opportunityBullish",
                "event": "market_trend_up",
                "severity": "info",
                "symbol": "BTCUSDT",
                "title": "BTCUSDT entered opportunity bullish",
            },
        )
    if channel == "signal.created":
        return WebSocketEvent(
            event=channel,
            timestamp=timestamp,
            data={"symbol": "BTCUSDT", "type": "longInflow", "score": 96, "confidence": 0.94},
        )
    if channel == "alert.triggered":
        return WebSocketEvent(
            event=channel,
            timestamp=timestamp,
            data={"alertId": "alert_001", "symbol": "BTCUSDT", "message": "Long inflow detected"},
        )
    if channel == "notification.sent":
        return WebSocketEvent(
            event=channel,
            timestamp=timestamp,
            data={"title": "Smart coin update", "body": "New realtime notification."},
        )
    return WebSocketEvent(
        event="error",
        timestamp=timestamp,
        data={"message": "Unsupported channel"},
    )
