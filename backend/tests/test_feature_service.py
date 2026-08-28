import pytest
from mip_common.events import MarketEvent
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService


@pytest.mark.asyncio
async def test_feature_service_calculates_features_from_ticker() -> None:
    service = FeatureService(InMemoryFeatureRepository())

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

    momentum = await service.get_current_feature("BTCUSDT", "price_momentum", "binance")
    long_inflow = await service.get_current_feature("BTCUSDT", "long_inflow_score", "binance")
    support = await service.get_current_feature("BTCUSDT", "support_level", "binance")
    resistance = await service.get_current_feature("BTCUSDT", "resistance_level", "binance")

    assert momentum.value == 2.5
    assert long_inflow.value == 55.0
    assert support.value < 68000
    assert resistance.value > 68000


@pytest.mark.asyncio
async def test_feature_service_interprets_pressure_support_levels() -> None:
    service = FeatureService(InMemoryFeatureRepository())

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

    interpretation = await service.pressure_support("BTCUSDT", "binance")

    assert interpretation.bias == "supportive"
    assert interpretation.mainForceRatio >= 20
    assert interpretation.supportLevel < interpretation.price
    assert interpretation.resistanceLevel > interpretation.price


@pytest.mark.asyncio
async def test_feature_service_derivatives_can_override_pressure_support_bias() -> None:
    service = FeatureService(InMemoryFeatureRepository())

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
    await service.calculate_from_derivatives(
        symbol="BTCUSDT",
        exchange="binance",
        timestamp=1700000001000,
        funding_rate=0.001,
        open_interest_change=30,
        long_liquidation_value=500_000,
        short_liquidation_value=50_000,
        taker_buy_value=100_000,
        taker_sell_value=900_000,
    )

    funding = await service.get_current_feature("BTCUSDT", "funding_pressure", "binance")
    interpretation = await service.pressure_support("BTCUSDT", "binance")

    assert funding.value == 100
    assert interpretation.bias == "pressure"


@pytest.mark.asyncio
async def test_feature_service_returns_history_with_time_filters() -> None:
    service = FeatureService(InMemoryFeatureRepository())
    for timestamp, change in [(1700000000000, 1.0), (1700000060000, 2.5)]:
        await service.calculate_from_market_ticker(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=timestamp,
                data={
                    "symbol": "BTCUSDT",
                    "price": 68000,
                    "change24h": change,
                    "volume24h": 120000000,
                },
            )
        )

    history = await service.get_history(
        "BTCUSDT",
        "price_momentum",
        exchange="binance",
        start_time=1700000060000,
        limit=10,
    )

    assert len(history) == 1
    assert history[0].value == 2.5
