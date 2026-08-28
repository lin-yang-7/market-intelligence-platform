import pytest
from mip_common.events import MarketEvent
from services.feature_service.app.repositories import RedisFeatureRepository
from services.feature_service.app.schemas import FeatureValue
from services.market_service.app.repositories import RedisTickerRepository
from services.market_service.app.schemas import KlineResponse, TradeResponse
from services.signal_service.app.repositories import RedisSignalRepository
from services.signal_service.app.schemas import Signal

from .fakes import FakeRedis


@pytest.mark.asyncio
async def test_redis_market_repository_stores_ticker_klines_and_trades() -> None:
    redis = FakeRedis()
    repository = RedisTickerRepository(redis)
    await repository.save_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000000000,
            data={"symbol": "BTCUSDT", "price": 68000},
        )
    )
    await repository.save_klines(
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
    await repository.save_trades(
        [
            TradeResponse(
                symbol="BTCUSDT",
                exchange="binance",
                tradeId="t1",
                price=68000,
                quantity=1,
                side="buy",
                timestamp=1700000001000,
            )
        ]
    )

    ticker = await repository.get_ticker("BTCUSDT", "binance")
    klines = await repository.list_klines("BTCUSDT", "1m", "binance")
    trades = await repository.list_trades("BTCUSDT", "binance")

    assert ticker is not None
    assert ticker.price == 68000
    assert klines[0].close == 67500
    assert trades[0].tradeId == "t1"


@pytest.mark.asyncio
async def test_redis_feature_repository_stores_latest_and_history() -> None:
    repository = RedisFeatureRepository(FakeRedis())
    await repository.save_features(
        [
            FeatureValue(
                symbol="BTCUSDT",
                exchange="binance",
                feature="price_momentum",
                value=2.5,
                timestamp=1700000000000,
            )
        ]
    )

    latest = await repository.get_feature("BTCUSDT", "price_momentum", "binance")
    history = await repository.list_history("BTCUSDT", "price_momentum", "binance")

    assert latest is not None
    assert latest.value == 2.5
    assert history[0].timestamp == 1700000000000


@pytest.mark.asyncio
async def test_redis_signal_repository_stores_current_detail_and_history() -> None:
    repository = RedisSignalRepository(FakeRedis())
    signal = Signal(
        signalId="sig_test",
        symbol="BTCUSDT",
        exchange="binance",
        type="longInflow",
        score=95,
        confidence=1,
        reasons=["high_inflow"],
        factors={"long_inflow_score": 95},
        explanation="test",
        timestamp=1700000000000,
    )
    await repository.save_signals([signal])

    current = await repository.list_current(signal_type="longInflow")
    detail = await repository.get_signal("sig_test")
    history = await repository.list_history("BTCUSDT", signal_type="longInflow")

    assert current[0].signalId == "sig_test"
    assert detail is not None
    assert detail.symbol == "BTCUSDT"
    assert history[0].score == 95

