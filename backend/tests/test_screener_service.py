import pytest
from mip_common.events import MarketEvent
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService
from services.screener_service.app.schemas import (
    CustomScreenerRequest,
    LongInflowScreenerRequest,
    ScreenerCondition,
    ScreenerQueryRequest,
)
from services.screener_service.app.services import ScreenerService


@pytest.mark.asyncio
async def test_screener_service_runs_long_inflow_preset() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    screener_service = ScreenerService(repository)
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

    results = await screener_service.long_inflow(
        LongInflowScreenerRequest(exchange="binance", minScore=90, minVolume=70)
    )

    assert results[0].symbol == "BTCUSDT"
    assert results[0].signals == ["high_inflow", "volume_breakout", "positive_momentum"]


@pytest.mark.asyncio
async def test_screener_service_runs_custom_conditions() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    screener_service = ScreenerService(repository)
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

    results = await screener_service.custom(
        CustomScreenerRequest(
            exchange="binance",
            conditions=[
                ScreenerCondition(feature="long_inflow_score", operator=">=", value=90),
            ],
        )
    )

    assert results[0].rank == 1
    assert results[0].factors["long_inflow_score"] == 100.0


@pytest.mark.asyncio
async def test_screener_service_rejects_invalid_type() -> None:
    screener_service = ScreenerService(InMemoryFeatureRepository())

    with pytest.raises(Exception) as exc_info:
        await screener_service.query(ScreenerQueryRequest(type="unknown"))

    assert exc_info.value.code == 5001

