import pytest
from mip_common.events import MarketEvent
from mip_common.models import model_to_dict
from mip_common.responses import ServiceError
from services.market_service.app.repositories import InMemoryTickerRepository
from services.market_service.app.schemas import (
    FundingRateResponse,
    KlineResponse,
    LiquidationResponse,
    OpenInterestResponse,
    TradeResponse,
)
from services.market_service.app.services import MarketService


@pytest.mark.asyncio
async def test_market_ticker_event_can_be_queried() -> None:
    repository = InMemoryTickerRepository()
    service = MarketService(repository)
    event = MarketEvent(
        event="market.ticker",
        exchange="binance",
        timestamp=1700000000000,
        data={
            "symbol": "BTCUSDT",
            "price": 68000.0,
            "change24h": 2.5,
            "volume24h": 120000000.0,
            "source": "test",
        },
    )

    await service.handle_market_ticker_event(event)
    ticker = await service.get_ticker("btcusdt", "BINANCE")

    assert model_to_dict(ticker)["symbol"] == "BTCUSDT"
    assert ticker.symbol == "BTCUSDT"
    assert ticker.exchange == "binance"
    assert ticker.price == 68000.0
    assert ticker.source == "test"


@pytest.mark.asyncio
async def test_missing_ticker_raises_symbol_not_found() -> None:
    service = MarketService(InMemoryTickerRepository())

    with pytest.raises(ServiceError) as exc_info:
        await service.get_ticker("BTCUSDT")

    assert exc_info.value.code == 3001


@pytest.mark.asyncio
async def test_invalid_exchange_is_rejected() -> None:
    service = MarketService(InMemoryTickerRepository())

    with pytest.raises(ServiceError) as exc_info:
        await service.get_ticker("BTCUSDT", "unknown")

    assert exc_info.value.code == 2002


@pytest.mark.asyncio
async def test_invalid_event_price_is_rejected() -> None:
    service = MarketService(InMemoryTickerRepository())

    with pytest.raises(ServiceError) as exc_info:
        await service.handle_market_ticker_event(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=1700000000000,
                data={"symbol": "BTCUSDT", "price": 0},
            )
        )

    assert exc_info.value.code == 2001


@pytest.mark.asyncio
async def test_market_service_queries_klines_and_trades() -> None:
    service = MarketService(InMemoryTickerRepository())
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

    klines = await service.get_klines("BTCUSDT", "1m", exchange="binance")
    trades = await service.get_trades("BTCUSDT", exchange="binance")

    assert klines[0].close == 67500
    assert trades[0].tradeId == "t1"


@pytest.mark.asyncio
async def test_market_service_queries_derivatives_data() -> None:
    service = MarketService(InMemoryTickerRepository())
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
                side="long",
                price=67000,
                quantity=2,
                value=134000,
                timestamp=1700000002000,
            )
        ]
    )

    funding = await service.get_funding_rates("BTCUSDT", exchange="binance")
    open_interest = await service.get_open_interest("BTCUSDT", exchange="binance")
    liquidations = await service.get_liquidations("BTCUSDT", exchange="binance")

    assert funding[0].fundingRate == 0.0001
    assert open_interest[0].changeRate == 5.2
    assert liquidations[0].side == "long"


@pytest.mark.asyncio
async def test_invalid_time_range_is_rejected() -> None:
    service = MarketService(InMemoryTickerRepository())

    with pytest.raises(ServiceError) as exc_info:
        await service.get_klines("BTCUSDT", "1m", start_time=2, end_time=1)

    assert exc_info.value.code == 2003
