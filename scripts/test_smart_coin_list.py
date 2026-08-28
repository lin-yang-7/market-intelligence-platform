import asyncio
import sys

from ai_engine.app.model import HybridScoringModel
from ai_engine.app.schemas import FeatureVector
from services.collector_service.app.connectors import create_ticker_connector
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService
from services.ranking_service.app.ai_scorer import AiScoreResult
from services.ranking_service.app.schemas import RankingItem
from services.ranking_service.app.services import RankingService

DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "LINKUSDT",
    "AVAXUSDT",
    "TRXUSDT",
]


class LocalAiScorer:
    def __init__(self) -> None:
        self.model = HybridScoringModel()

    async def score(
        self,
        symbol: str,
        exchange: str,
        factors: dict[str, float],
    ) -> AiScoreResult:
        prediction = self.model.predict(
            symbol=symbol,
            exchange=exchange,
            features=FeatureVector(
                capital_flow=max(-1.0, factors.get("long_inflow_score", 0.0) / 100)
                * 5_000_000_000,
                volume_imbalance=max(-1.0, min(1.0, factors.get("volume_activity", 0.0) / 50 - 1)),
                price_momentum=max(-1.0, min(1.0, factors.get("price_momentum", 0.0) / 100)),
                volatility=max(0.0, min(1.0, abs(factors.get("price_momentum", 0.0)) / 100)),
                liquidity=max(0.0, min(1.0, factors.get("volume_activity", 0.0) / 100))
                * 2_000_000_000,
            ),
        )
        return AiScoreResult(
            modelVersion=prediction.model_version,
            opportunityScore=prediction.opportunity_score,
            riskScore=prediction.risk_score,
            confidence=prediction.confidence,
            overallScore=prediction.overall_score,
            riskWarning=prediction.risk_warning,
            factors={
                f"ai_{factor.factor}": factor.contribution
                for factor in prediction.factors
            },
        )


def abnormal_bullish_score(item: RankingItem) -> float:
    momentum = item.factors.get("price_momentum", 0.0)
    volume = item.factors.get("volume_activity", 0.0)
    return round(max(0.0, momentum) * 12 + volume * 0.45, 2)


def opportunity_bullish_score(item: RankingItem) -> float:
    opportunity = item.opportunityScore or item.score
    return round(item.score * 0.55 + opportunity * 0.3 + item.confidence * 100 * 0.15, 2)


def risk_bearish_score(item: RankingItem) -> float:
    momentum = item.factors.get("price_momentum", 0.0)
    downside = max(0.0, -momentum) * 12
    risk = item.riskScore or 0.0
    weak_opportunity = max(0.0, 70 - item.score) * 0.4
    return round(risk + downside + weak_opportunity, 2)


def print_list(title: str, rows: list[tuple[RankingItem, float]], threshold: float) -> None:
    print()
    print(title)
    print("Rank  Symbol    Price        24h%    ListScore  AIScore  Risk")
    print("----  --------  -----------  ------  ---------  -------  ----")
    filtered = [(item, score) for item, score in rows if score >= threshold]
    for rank, (item, list_score) in enumerate(filtered[:5], start=1):
        price = item.factors.get("last_price", 0.0)
        change = item.factors.get("price_momentum", 0.0)
        print(
            f"{rank:<4}  "
            f"{item.symbol:<8}  "
            f"{price:>11.4f}  "
            f"{change:>5.1f}%  "
            f"{list_score:>9.1f}  "
            f"{item.score:>7.1f}  "
            f"{(item.riskScore or 0):>4.1f}"
        )
    if not filtered:
        print("没有命中")


async def main() -> None:
    feature_repository = InMemoryFeatureRepository()
    feature_service = FeatureService(feature_repository)
    ranking_service = RankingService(feature_repository, LocalAiScorer())
    connector = create_ticker_connector("binance")
    symbols = [symbol.upper() for symbol in sys.argv[1:]] or DEFAULT_SYMBOLS

    for symbol in symbols:
        event = await connector.fetch_ticker(symbol)
        await feature_service.calculate_from_market_ticker(event)

    ranking = await ranking_service.get_ranking("longInflow", exchange="binance", limit=10)
    abnormal_rows = sorted(
        [(item, abnormal_bullish_score(item)) for item in ranking],
        key=lambda row: row[1],
        reverse=True,
    )
    opportunity_rows = sorted(
        [(item, opportunity_bullish_score(item)) for item in ranking],
        key=lambda row: row[1],
        reverse=True,
    )
    risk_rows = sorted(
        [(item, risk_bearish_score(item)) for item in ranking],
        key=lambda row: row[1],
        reverse=True,
    )

    print("Binance 实时智能选币测试")
    print(f"Symbols: {', '.join(symbols)}")
    print_list("异动看涨榜", abnormal_rows, threshold=45)
    print_list("机会看涨榜", opportunity_rows, threshold=70)
    print_list("风险看跌榜", risk_rows, threshold=25)


if __name__ == "__main__":
    asyncio.run(main())
