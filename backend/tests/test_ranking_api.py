import asyncio

from fastapi.testclient import TestClient
from mip_common.events import MarketEvent
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.schemas import FeatureValue
from services.feature_service.app.services import FeatureService
from services.ranking_service.app.dependencies import get_ranking_service
from services.ranking_service.app.main import app
from services.ranking_service.app.score_client import ScoreClientResult
from services.ranking_service.app.services import RankingService


class FakeScoreClient:
    async def score(
        self,
        score_type: str,
        symbol: str,
        exchange: str,
        factors: dict[str, float],
    ) -> ScoreClientResult:
        return ScoreClientResult(
            score=97.5,
            confidence=0.92,
            factors={**factors, "score_service": 1.0},
            modelVersion="score-test",
        )


def test_ranking_long_inflow_endpoint_returns_ranked_items() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    ranking_service = RankingService(repository)

    async def seed() -> None:
        await feature_service.calculate_from_market_ticker(
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

    asyncio.run(seed())
    app.dependency_overrides[get_ranking_service] = lambda: ranking_service
    try:
        response = TestClient(app).get(
            "/v1/ranking/longInflow",
            params={"exchange": "binance", "limit": 10},
            headers={"X-Request-ID": "ranking-test"},
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == 0
    assert payload["requestId"] == "ranking-test"
    assert payload["data"][0]["symbol"] == "BTCUSDT"
    assert payload["data"][0]["rank"] == 1


def test_ranking_service_prefers_score_service_result() -> None:
    repository = InMemoryFeatureRepository()

    async def run() -> list:
        await repository.save_features(
            [
                FeatureValue(
                    symbol="BTCUSDT",
                    exchange="binance",
                    feature="long_inflow_score",
                    value=10,
                    timestamp=1700000000000,
                )
            ]
        )
        return await RankingService(
            repository,
            score_client=FakeScoreClient(),
        ).get_ranking("longInflow")

    items = asyncio.run(run())

    assert items[0].score == 97.5
    assert items[0].confidence == 0.92
    assert items[0].modelVersion == "score-test"
    assert items[0].factors["score_service"] == 1.0


def test_ranking_monitor_endpoint_returns_membership_changes() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    ranking_service = RankingService(repository)

    async def seed() -> None:
        await feature_service.calculate_from_market_ticker(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=1700000000000,
                data={
                    "symbol": "BTCUSDT",
                    "price": 68000,
                    "change24h": 7,
                    "volume24h": 120000000,
                },
            )
        )

    asyncio.run(seed())
    app.dependency_overrides[get_ranking_service] = lambda: ranking_service
    try:
        response = TestClient(app).post(
            "/v1/ranking/monitor/opportunityBullish",
            params={"exchange": "binance", "limit": 10, "min_score": 50, "max_score": 100},
            headers={"X-Request-ID": "ranking-monitor-test"},
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == 0
    assert payload["requestId"] == "ranking-monitor-test"
    assert payload["data"]["rankingType"] == "opportunityBullish"
    assert payload["data"]["changes"]["entered"][0]["symbol"] == "BTCUSDT"
