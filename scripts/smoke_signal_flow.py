import asyncio

from mip_common.models import model_to_dict
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService
from services.ranking_service.app.services import RankingService
from services.signal_service.app.repositories import InMemorySignalRepository
from services.signal_service.app.services import SignalService


async def main() -> None:
    from mip_common.events import MarketEvent

    feature_repository = InMemoryFeatureRepository()
    feature_service = FeatureService(feature_repository)
    ranking_service = RankingService(feature_repository)
    signal_service = SignalService(InMemorySignalRepository())

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
    ranking = await ranking_service.get_ranking("longInflow", exchange="binance", limit=10)
    signals = await signal_service.generate_from_ranking("longInflow", ranking)
    print([model_to_dict(signal) for signal in signals])


if __name__ == "__main__":
    asyncio.run(main())
