from fastapi.testclient import TestClient
from mip_common.events import MarketEvent
from services.market_service.app.dependencies import get_market_service
from services.market_service.app.main import app
from services.market_service.app.repositories import InMemoryTickerRepository
from services.market_service.app.schemas import (
    FundingRateResponse,
    KlineResponse,
    LiquidationResponse,
    OpenInterestResponse,
    TradeResponse,
)
from services.market_service.app.services import MarketService


def test_market_ticker_endpoint_returns_standard_response() -> None:
    service = MarketService(InMemoryTickerRepository())

    async def seed() -> None:
        await service.handle_market_ticker_event(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=1700000000000,
                data={
                    "symbol": "BTCUSDT",
                    "price": 68000,
                    "change24h": 2.5,
                    "volume24h": 120000000,
                    "source": "api-test",
                },
            )
        )

    import asyncio

    asyncio.run(seed())
    app.dependency_overrides[get_market_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/v1/market/ticker",
            params={"symbol": "BTCUSDT", "exchange": "binance"},
            headers={"X-Request-ID": "test-request"},
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == 0
    assert payload["requestId"] == "test-request"
    assert payload["data"]["symbol"] == "BTCUSDT"
    assert payload["data"]["source"] == "api-test"


def test_market_ticker_endpoint_returns_error_response() -> None:
    app.dependency_overrides[get_market_service] = lambda: MarketService(InMemoryTickerRepository())
    try:
        response = TestClient(app).get(
            "/v1/market/ticker",
            params={"symbol": "BTCUSDT", "exchange": "unknown"},
            headers={"X-Request-ID": "test-request"},
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 400
    assert payload["code"] == 2002
    assert payload["requestId"] == "test-request"


def test_market_kline_and_trades_endpoints_return_standard_response() -> None:
    service = MarketService(InMemoryTickerRepository())

    async def seed() -> None:
        await service.save_klines(
            [
                KlineResponse(
                    symbol="BTCUSDT",
                    exchange="binance",
                    interval="1m",
                    timestamp=1700000000000,
                    open=67000,
                    high=68000,
                    low=66500,
                    close=67500,
                    volume=10000,
                )
            ]
        )
        await service.save_trades(
            [
                TradeResponse(
                    symbol="BTCUSDT",
                    exchange="binance",
                    tradeId="t1",
                    price=68000,
                    quantity=1.2,
                    side="buy",
                    timestamp=1700000001000,
                )
            ]
        )

    import asyncio

    asyncio.run(seed())
    app.dependency_overrides[get_market_service] = lambda: service
    try:
        kline_response = TestClient(app).get(
            "/v1/market/kline",
            params={"symbol": "BTCUSDT", "exchange": "binance", "interval": "1m"},
            headers={"X-Request-ID": "kline-test"},
        )
        trades_response = TestClient(app).get(
            "/v1/market/trades",
            params={"symbol": "BTCUSDT", "exchange": "binance"},
            headers={"X-Request-ID": "trades-test"},
        )
    finally:
        app.dependency_overrides.clear()

    assert kline_response.status_code == 200
    assert kline_response.json()["requestId"] == "kline-test"
    assert kline_response.json()["data"][0]["close"] == 67500
    assert trades_response.status_code == 200
    assert trades_response.json()["requestId"] == "trades-test"
    assert trades_response.json()["data"][0]["tradeId"] == "t1"


def test_market_derivatives_endpoints_return_standard_response() -> None:
    service = MarketService(InMemoryTickerRepository())

    async def seed() -> None:
        await service.save_funding_rates(
            [
                FundingRateResponse(
                    symbol="BTCUSDT",
                    exchange="binance",
                    fundingRate=0.0001,
                    nextFundingTime=1700007200000,
                    timestamp=1700000000000,
                )
            ]
        )
        await service.save_open_interest(
            [
                OpenInterestResponse(
                    symbol="BTCUSDT",
                    exchange="binance",
                    openInterest=1_000_000_000,
                    changeRate=5.2,
                    timestamp=1700000001000,
                )
            ]
        )
        await service.save_liquidations(
            [
                LiquidationResponse(
                    symbol="BTCUSDT",
                    exchange="binance",
                    side="short",
                    price=69000,
                    quantity=1.5,
                    value=103500,
                    timestamp=1700000002000,
                )
            ]
        )

    import asyncio

    asyncio.run(seed())
    app.dependency_overrides[get_market_service] = lambda: service
    try:
        client = TestClient(app)
        funding_response = client.get(
            "/v1/market/funding",
            params={"symbol": "BTCUSDT", "exchange": "binance"},
            headers={"X-Request-ID": "funding-test"},
        )
        open_interest_response = client.get(
            "/v1/market/openInterest",
            params={"symbol": "BTCUSDT", "exchange": "binance"},
            headers={"X-Request-ID": "open-interest-test"},
        )
        liquidation_response = client.get(
            "/v1/market/liquidation",
            params={"symbol": "BTCUSDT", "exchange": "binance"},
            headers={"X-Request-ID": "liquidation-test"},
        )
    finally:
        app.dependency_overrides.clear()

    assert funding_response.status_code == 200
    assert funding_response.json()["data"][0]["fundingRate"] == 0.0001
    assert open_interest_response.status_code == 200
    assert open_interest_response.json()["data"][0]["openInterest"] == 1_000_000_000
    assert liquidation_response.status_code == 200
    assert liquidation_response.json()["data"][0]["side"] == "short"
