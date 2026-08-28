import asyncio

from mip_common.events import MarketEvent
from mip_common.models import model_to_dict
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService
from services.screener_service.app.schemas import CustomScreenerRequest, ScreenerCondition
from services.screener_service.app.services import ScreenerService


async def main() -> None:
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
                ScreenerCondition(feature="volume_activity", operator=">=", value=70),
            ],
        )
    )
    print([model_to_dict(item) for item in results])


if __name__ == "__main__":
    asyncio.run(main())
