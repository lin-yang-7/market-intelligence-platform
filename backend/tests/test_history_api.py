from typing import Any

from fastapi.testclient import TestClient
from services.history_service.app.dependencies import get_history_service
from services.history_service.app.main import app
from services.history_service.app.services import HistoryService


class FakeHistorySource:
    async def get(self, base_url: str, path: str, params: dict[str, Any]) -> Any:
        if path == "/v1/market/kline":
            return [
                {
                    "exchange": "binance",
                    "symbol": params["symbol"].upper(),
                    "interval": params["interval"],
                    "open": 68000,
                    "high": 69000,
                    "low": 67500,
                    "close": 68800,
                    "volume": 1200,
                    "timestamp": 1700000000000,
                }
            ]
        if path == "/v1/feature/history":
            return [
                {
                    "exchange": "binance",
                    "symbol": params["symbol"].upper(),
                    "feature": params["feature"],
                    "value": 88.5,
                    "version": "v1",
                    "timestamp": 1700000001000,
                }
            ]
        if path == "/v1/signal/history":
            return [
                {
                    "signalId": "sig_btc",
                    "exchange": "binance",
                    "symbol": params["symbol"].upper(),
                    "type": "longInflow",
                    "score": 91,
                    "confidence": 0.9,
                    "reasons": ["high_inflow"],
                    "timestamp": 1700000002000,
                }
            ]
        if path == "/v1/data/ranking-monitor/events":
            return [
                {
                    "exchange": params.get("exchange", "binance"),
                    "symbol": "BTCUSDT",
                    "rankingType": params["rankingType"],
                    "eventAction": "market_trend_up",
                    "fromRank": 0,
                    "toRank": 1,
                    "score": 72.5,
                    "previousScore": 0,
                    "scoreChange": 0,
                    "marketBias": "uptrend",
                    "summary": {
                        "title": "BTCUSDT entered opportunity bullish",
                        "body": "BTC entered the opportunity monitor.",
                        "severity": "info",
                    },
                    "timestamp": 1700000003000,
                }
            ]
        raise AssertionError(path)


def test_history_snapshot_endpoint_returns_merged_series_and_timeline() -> None:
    service = HistoryService(
        source=FakeHistorySource(),
        market_service_url="market",
        feature_service_url="feature",
        signal_service_url="signal",
    )
    app.dependency_overrides[get_history_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/v1/history/snapshot",
            params={"symbol": "BTCUSDT", "features": "long_inflow_score", "limit": 10},
            headers={"X-Request-ID": "history-test"},
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == 0
    assert payload["requestId"] == "history-test"
    assert payload["data"]["symbol"] == "BTCUSDT"
    assert [series["name"] for series in payload["data"]["series"]] == [
        "price",
        "long_inflow_score",
        "signals",
    ]
    assert payload["data"]["timeline"][0]["source"] == "signal"
    assert payload["data"]["timeline"][1]["source"] == "feature"
    assert payload["data"]["timeline"][2]["source"] == "market"


def test_history_timeline_endpoint_returns_events_only() -> None:
    service = HistoryService(
        source=FakeHistorySource(),
        market_service_url="market",
        feature_service_url="feature",
        signal_service_url="signal",
    )
    app.dependency_overrides[get_history_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/v1/history/timeline",
            params={"symbol": "BTCUSDT", "features": "long_inflow_score"},
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"][0]["timestamp"] == 1700000002000
    assert len(payload["data"]) == 3


def test_history_ranking_monitor_events_endpoint_returns_data_platform_events() -> None:
    service = HistoryService(
        source=FakeHistorySource(),
        market_service_url="market",
        feature_service_url="feature",
        signal_service_url="signal",
        data_platform_url="data-platform",
    )
    app.dependency_overrides[get_history_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/v1/history/ranking-monitor/events",
            params={"rankingType": "opportunityBullish", "limit": 10},
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"][0]["eventAction"] == "market_trend_up"
    assert payload["data"][0]["summary"]["severity"] == "info"
