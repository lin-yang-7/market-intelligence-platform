import pytest
from services.ranking_service.app.monitor_worker import (
    MonitorWorkerConfig,
    RankingMonitorWorker,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class FakeHttpClient:
    def __init__(self, snapshots: dict[str, dict]) -> None:
        self.snapshots = snapshots
        self.calls: list[tuple[str, dict | None]] = []

    async def post(self, url: str, params: dict | None = None, json: dict | None = None):
        self.calls.append((url, params or json))
        ranking_type = url.rsplit("/", 1)[-1]
        return FakeResponse({"data": self.snapshots[ranking_type]})


class FakePublisher:
    def __init__(self) -> None:
        self.websocket_events: list[tuple[str, dict]] = []
        self.notifications: list[tuple[str, str, dict]] = []
        self.stored_events: list[tuple[str, dict, int]] = []

    async def publish_websocket(self, event: str, data: dict) -> None:
        self.websocket_events.append((event, data))

    async def publish_sse_notification(self, title: str, body: str, metadata: dict) -> None:
        self.notifications.append((title, body, metadata))

    async def store_event(self, event: str, data: dict, timestamp: int) -> None:
        self.stored_events.append((event, data, timestamp))


def snapshot(changes: dict) -> dict:
    return {
        "rankingType": "opportunityBullish",
        "exchange": "binance",
        "updatedAt": 1700000000000,
        "active": [{"symbol": "BTCUSDT"}],
        "changes": changes,
        "summary": {"marketBias": "uptrend"},
    }


@pytest.mark.asyncio
async def test_ranking_monitor_worker_publishes_change_events() -> None:
    client = FakeHttpClient(
        {
            "opportunityBullish": snapshot(
                {
                    "entered": [{"symbol": "BTCUSDT", "toRank": 1}],
                    "exited": [{"symbol": "ETHUSDT", "fromRank": 2}],
                    "moved": [{"symbol": "SOLUSDT", "fromRank": 3, "toRank": 2}],
                    "strategyEvents": [
                        {
                            "event": "market_trend_up",
                            "severity": "info",
                            "symbol": "BTCUSDT",
                            "title": "BTCUSDT entered opportunity bullish",
                            "body": "BTC entered the opportunity monitor.",
                        }
                    ],
                }
            )
        }
    )
    publisher = FakePublisher()
    worker = RankingMonitorWorker(
        client,
        publisher,
        MonitorWorkerConfig(
            ranking_service_url="http://ranking-service:8004",
            websocket_service_url="http://websocket-service:8008",
            data_platform_url="http://data-platform:8011",
            notification_service_url="http://notification-service:8012",
            exchange="binance",
            ranking_types=["opportunityBullish"],
            interval_seconds=60,
            limit=50,
        ),
    )

    await worker.run_once()

    assert [event for event, _data in publisher.websocket_events] == [
        "ranking.monitor.updated",
        "ranking.entered",
        "ranking.exited",
        "ranking.moved",
        "ranking.strategy",
    ]
    assert publisher.websocket_events[1][1]["symbol"] == "BTCUSDT"
    assert publisher.notifications[0][0] == "opportunityBullish monitor changed"
    assert publisher.notifications[0][2]["enteredCount"] == 1
    assert publisher.notifications[0][2]["strategyEventCount"] == 1
    assert [event for event, _data, _timestamp in publisher.stored_events] == [
        "ranking.entered",
        "ranking.exited",
        "ranking.moved",
        "ranking.strategy",
    ]
    assert publisher.stored_events[0][1]["summary"]["marketBias"] == "uptrend"
    assert publisher.stored_events[-1][1]["event"] == "market_trend_up"


@pytest.mark.asyncio
async def test_ranking_monitor_worker_skips_publish_without_changes() -> None:
    client = FakeHttpClient(
        {
            "opportunityBullish": snapshot(
                {
                    "entered": [],
                    "exited": [],
                    "moved": [],
                }
            )
        }
    )
    publisher = FakePublisher()
    worker = RankingMonitorWorker(
        client,
        publisher,
        MonitorWorkerConfig(
            ranking_service_url="http://ranking-service:8004",
            websocket_service_url="http://websocket-service:8008",
            data_platform_url="http://data-platform:8011",
            notification_service_url="http://notification-service:8012",
            exchange="binance",
            ranking_types=["opportunityBullish"],
            interval_seconds=60,
            limit=50,
        ),
    )

    await worker.run_once()

    assert publisher.websocket_events == []
    assert publisher.notifications == []
