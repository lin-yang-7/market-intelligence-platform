from fastapi.testclient import TestClient
from mip_common.events import MarketEvent
from services.feature_service.app.dependencies import get_feature_service
from services.feature_service.app.main import app
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService


def test_feature_list_endpoint_returns_definitions() -> None:
    response = TestClient(app).get("/v1/feature/list", headers={"X-Request-ID": "feature-list"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == 0
    assert payload["requestId"] == "feature-list"
    assert {item["name"] for item in payload["data"]} >= {
        "price_momentum",
        "volume_activity",
        "long_inflow_score",
        "main_force_net_inflow",
        "support_level",
        "resistance_level",
        "funding_pressure",
        "open_interest_change",
        "liquidation_pressure",
        "taker_buy_sell_imbalance",
    }


def test_feature_batch_endpoint_returns_feature_values() -> None:
    service = FeatureService(InMemoryFeatureRepository())

    async def seed() -> None:
        await service.calculate_from_market_ticker(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=1700000000000,
                data={
                    "symbol": "BTCUSDT",
                    "price": 68000,
                    "change24h": 2.5,
                    "volume24h": 120000000,
                },
            )
        )

    import asyncio

    asyncio.run(seed())
    app.dependency_overrides[get_feature_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/v1/feature/batch",
            params={
                "symbol": "BTCUSDT",
                "exchange": "binance",
                "features": "price_momentum,long_inflow_score",
            },
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"]["features"]["price_momentum"] == 2.5
    assert payload["data"]["features"]["long_inflow_score"] == 55.0


def test_feature_history_endpoint_returns_values() -> None:
    service = FeatureService(InMemoryFeatureRepository())

    async def seed() -> None:
        await service.calculate_from_market_ticker(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=1700000000000,
                data={
                    "symbol": "BTCUSDT",
                    "price": 68000,
                    "change24h": 2.5,
                    "volume24h": 120000000,
                },
            )
        )

    import asyncio

    asyncio.run(seed())
    app.dependency_overrides[get_feature_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/v1/feature/history",
            params={
                "symbol": "BTCUSDT",
                "exchange": "binance",
                "feature": "price_momentum",
            },
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"][0]["value"] == 2.5


def test_pressure_support_endpoint_returns_interpretation() -> None:
    service = FeatureService(InMemoryFeatureRepository())

    async def seed() -> None:
        await service.calculate_from_market_ticker(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=1700000000000,
                data={
                    "symbol": "BTCUSDT",
                    "price": 68000,
                    "change24h": 4.0,
                    "volume24h": 120000000,
                },
            )
        )

    import asyncio

    asyncio.run(seed())
    app.dependency_overrides[get_feature_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/v1/feature/pressure-support",
            params={
                "symbol": "BTCUSDT",
                "exchange": "binance",
            },
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"]["bias"] == "supportive"
    assert payload["data"]["supportLevel"] < payload["data"]["price"]
    assert payload["data"]["resistanceLevel"] > payload["data"]["price"]
