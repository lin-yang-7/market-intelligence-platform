import asyncio

from fastapi.testclient import TestClient
from mip_common.events import MarketEvent
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService
from services.screener_service.app.dependencies import get_screener_service
from services.screener_service.app.main import app
from services.screener_service.app.services import ScreenerService


def test_screener_list_endpoint_returns_presets() -> None:
    response = TestClient(app).get("/v1/screener/list", headers={"X-Request-ID": "screener-list"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["requestId"] == "screener-list"
    assert {item["type"] for item in payload["data"]} >= {"longInflow", "momentum", "volume"}


def test_screener_custom_endpoint_returns_matches() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    screener_service = ScreenerService(repository)

    async def seed() -> None:
        await feature_service.calculate_from_market_ticker(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=1700000000000,
                data={
                    "symbol": "BTCUSDT",
                    "price": 68000,
                    "change24h": 8.0,
                    "volume24h": 300000000,
                },
            )
        )

    asyncio.run(seed())
    app.dependency_overrides[get_screener_service] = lambda: screener_service
    try:
        response = TestClient(app).post(
            "/v1/screener/custom",
            json={
                "exchange": "binance",
                "conditions": [
                    {"feature": "long_inflow_score", "operator": ">=", "value": 90},
                    {"feature": "volume_activity", "operator": ">=", "value": 70},
                ],
            },
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == 0
    assert payload["data"][0]["symbol"] == "BTCUSDT"

