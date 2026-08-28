import pytest
from services.ranking_service.app.schemas import RankingItem
from services.signal_service.app.repositories import InMemorySignalRepository
from services.signal_service.app.services import SignalService


@pytest.mark.asyncio
async def test_signal_service_generates_long_inflow_signal_from_ranking() -> None:
    service = SignalService(InMemorySignalRepository())
    ranking = [
        RankingItem(
            rank=1,
            symbol="BTCUSDT",
            exchange="binance",
            score=95.0,
            confidence=1.0,
            timestamp=1700000000000,
            factors={
                "long_inflow_score": 95.0,
                "volume_activity": 90.0,
                "price_momentum": 5.0,
            },
        )
    ]

    signals = await service.generate_from_ranking("longInflow", ranking)
    current = await service.current(signal_type="longInflow")
    detail = await service.detail(signals[0].signalId)

    assert signals[0].type == "longInflow"
    assert signals[0].score == 95.0
    assert signals[0].reasons == ["high_inflow", "volume_breakout", "positive_momentum"]
    assert current[0].signalId == signals[0].signalId
    assert detail.symbol == "BTCUSDT"


@pytest.mark.asyncio
async def test_signal_service_ignores_weak_ranking_items() -> None:
    service = SignalService(InMemorySignalRepository())
    ranking = [
        RankingItem(
            rank=1,
            symbol="ETHUSDT",
            exchange="binance",
            score=69.0,
            confidence=1.0,
            timestamp=1700000000000,
            factors={"long_inflow_score": 69.0},
        )
    ]

    signals = await service.generate_from_ranking("longInflow", ranking)

    assert signals == []


@pytest.mark.asyncio
async def test_signal_service_history_supports_time_filters() -> None:
    service = SignalService(InMemorySignalRepository())
    await service.generate_from_ranking(
        "longInflow",
        [
            RankingItem(
                rank=1,
                symbol="BTCUSDT",
                exchange="binance",
                score=95.0,
                confidence=1.0,
                timestamp=1700000000000,
                factors={"long_inflow_score": 95.0},
            ),
            RankingItem(
                rank=2,
                symbol="BTCUSDT",
                exchange="binance",
                score=96.0,
                confidence=1.0,
                timestamp=1700000060000,
                factors={"long_inflow_score": 96.0},
            ),
        ],
    )

    history = await service.history(
        "BTCUSDT",
        signal_type="longInflow",
        start_time=1700000060000,
        end_time=1700000060000,
    )

    assert len(history) == 1
    assert history[0].score == 96.0
