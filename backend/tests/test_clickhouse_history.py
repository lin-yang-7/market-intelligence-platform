import pytest
from mip_common.history import (
    ClickHouseFeatureHistoryRepository,
    ClickHouseMarketHistoryRepository,
    ClickHouseSignalHistoryRepository,
)
from services.feature_service.app.schemas import FeatureValue
from services.market_service.app.schemas import KlineResponse, TradeResponse
from services.signal_service.app.schemas import Signal

from .fakes import FakeClickHouseClient


@pytest.mark.asyncio
async def test_clickhouse_market_history_repository_stores_klines_and_trades() -> None:
    client = FakeClickHouseClient()
    repository = ClickHouseMarketHistoryRepository(client)

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
                timestamp=1700000000000,
            )
        ]
    )
    klines = await repository.list_klines(KlineResponse, "BTCUSDT", "1m", "binance")

    assert client.tables["market_trade"][0]["trade_id"] == "t1"
    assert klines[0].close == 67500


@pytest.mark.asyncio
async def test_clickhouse_feature_and_signal_history_repositories_round_trip() -> None:
    client = FakeClickHouseClient()
    feature_repository = ClickHouseFeatureHistoryRepository(client)
    signal_repository = ClickHouseSignalHistoryRepository(client)

    await feature_repository.save_features(
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
    await signal_repository.save_signals(
        [
            Signal(
                signalId="sig_test",
                symbol="BTCUSDT",
                exchange="binance",
                type="longInflow",
                score=95,
                confidence=1,
                reasons=["high_inflow"],
                factors={},
                explanation="test",
                timestamp=1700000000000,
            )
        ]
    )

    features = await feature_repository.list_history(
        FeatureValue,
        "BTCUSDT",
        "price_momentum",
        "binance",
    )
    signals = await signal_repository.list_history(Signal, "BTCUSDT", "longInflow")

    assert features[0].value == 2.5
    assert signals[0].signalId == "sig_test"

