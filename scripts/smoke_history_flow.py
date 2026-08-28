import asyncio

from mip_common.events import MarketEvent
from mip_common.models import model_to_dict
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService
from services.ranking_service.app.schemas import RankingItem
from services.signal_service.app.repositories import InMemorySignalRepository
from services.signal_service.app.services import SignalService


async def main() -> None:
    feature_service = FeatureService(InMemoryFeatureRepository())
    signal_service = SignalService(InMemorySignalRepository())

    for timestamp, change in [(1700000000000, 1.0), (1700000060000, 2.5)]:
        await feature_service.calculate_from_market_ticker(
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

    await signal_service.generate_from_ranking(
        "longInflow",
        [
            RankingItem(
                rank=1,
                symbol="BTCUSDT",
                exchange="binance",
                score=95.0,
                confidence=1.0,
                timestamp=1700000060000,
                factors={"long_inflow_score": 95.0, "volume_activity": 90.0},
            )
        ],
    )

    feature_history = await feature_service.get_history(
        "BTCUSDT",
        "price_momentum",
        exchange="binance",
        limit=10,
    )
    signal_history = await signal_service.history(
        "BTCUSDT",
        signal_type="longInflow",
        start_time=1700000000000,
        end_time=1700000060000,
    )
    print([model_to_dict(item) for item in feature_history])
    print([model_to_dict(item) for item in signal_history])


if __name__ == "__main__":
    asyncio.run(main())
