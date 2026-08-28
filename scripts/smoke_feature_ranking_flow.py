import asyncio

from mip_common.models import model_to_dict
from services.collector_service.app.connectors import create_ticker_connector
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService
from services.ranking_service.app.services import RankingService


async def main() -> None:
    connector = create_ticker_connector("mock")
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    ranking_service = RankingService(repository)

    for symbol in ["BTCUSDT", "ETHUSDT"]:
        event = await connector.fetch_ticker(symbol)
        await feature_service.calculate_from_market_ticker(event)

    ranking = await ranking_service.get_ranking("overall", limit=10)
    print([model_to_dict(item) for item in ranking])


if __name__ == "__main__":
    asyncio.run(main())
