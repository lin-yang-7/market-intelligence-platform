import asyncio

from mip_common.events import MarketEvent
from mip_common.models import model_to_dict
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService
from services.ranking_service.app.ai_scorer import AiScoreResult
from services.ranking_service.app.services import RankingService
from services.signal_service.app.repositories import InMemorySignalRepository
from services.signal_service.app.services import SignalService


class FakeAiScorer:
    async def score(
        self,
        symbol: str,
        exchange: str,
        factors: dict[str, float],
    ) -> AiScoreResult:
        return AiScoreResult(
            modelVersion="fake-ai-v1",
            opportunityScore=94.0,
            riskScore=18.0,
            confidence=0.91,
            overallScore=90.2,
            riskWarning="Risk level is within the MVP model tolerance.",
            factors={"ai_capital_flow": 24.0, "ai_price_momentum": 18.0},
        )


async def main() -> None:
    feature_repository = InMemoryFeatureRepository()
    feature_service = FeatureService(feature_repository)
    ranking_service = RankingService(feature_repository, FakeAiScorer())
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
    print([model_to_dict(item) for item in ranking])
    print([model_to_dict(signal) for signal in signals])


if __name__ == "__main__":
    asyncio.run(main())
