import asyncio

from fastapi.testclient import TestClient
from services.ranking_service.app.schemas import RankingItem
from services.signal_service.app.dependencies import get_signal_service
from services.signal_service.app.main import app
from services.signal_service.app.repositories import InMemorySignalRepository
from services.signal_service.app.services import SignalService


def test_signal_current_and_detail_endpoints_return_standard_response() -> None:
    service = SignalService(InMemorySignalRepository())

    async def seed() -> str:
        signals = await service.generate_from_ranking(
            "longInflow",
            [
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
            ],
        )
        return signals[0].signalId

    signal_id = asyncio.run(seed())
    app.dependency_overrides[get_signal_service] = lambda: service
    try:
        current_response = TestClient(app).get(
            "/v1/signal/current",
            params={"type": "longInflow"},
            headers={"X-Request-ID": "signal-current"},
        )
        detail_response = TestClient(app).get(
            "/v1/signal/detail",
            params={"signalId": signal_id},
            headers={"X-Request-ID": "signal-detail"},
        )
    finally:
        app.dependency_overrides.clear()

    current_payload = current_response.json()
    detail_payload = detail_response.json()
    assert current_response.status_code == 200
    assert current_payload["code"] == 0
    assert current_payload["requestId"] == "signal-current"
    assert current_payload["data"][0]["signalId"] == signal_id
    assert detail_response.status_code == 200
    assert detail_payload["data"]["symbol"] == "BTCUSDT"


def test_signal_history_endpoint_supports_time_filters() -> None:
    service = SignalService(InMemorySignalRepository())

    async def seed() -> None:
        await service.generate_from_ranking(
            "longInflow",
            [
                RankingItem(
                    rank=1,
                    symbol="BTCUSDT",
                    exchange="binance",
                    score=95.0,
                    confidence=1.0,
                    timestamp=1700000060000,
                    factors={"long_inflow_score": 95.0},
                )
            ],
        )

    signal_id = None
    asyncio.run(seed())
    app.dependency_overrides[get_signal_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/v1/signal/history",
            params={
                "symbol": "BTCUSDT",
                "type": "longInflow",
                "startTime": 1700000060000,
                "endTime": 1700000060000,
            },
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert signal_id is None
    assert response.status_code == 200
    assert payload["data"][0]["score"] == 95.0


def test_internal_signal_generation_requires_internal_token() -> None:
    service = SignalService(InMemorySignalRepository())
    ranking = {
        "rank": 1,
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "score": 91.0,
        "confidence": 0.9,
        "timestamp": 1700000000000,
        "factors": {"long_inflow_score": 91.0},
    }
    app.dependency_overrides[get_signal_service] = lambda: service
    try:
        forbidden = TestClient(app).post(
            "/internal/signals/generate",
            json={"rankingType": "longInflow", "ranking": [ranking]},
        )
        accepted = TestClient(app).post(
            "/internal/signals/generate",
            headers={"X-Internal-Service-Token": "local-internal-service-token"},
            json={"rankingType": "longInflow", "ranking": [ranking]},
        )
    finally:
        app.dependency_overrides.clear()

    assert forbidden.status_code == 400
    assert forbidden.json()["code"] == 1001
    assert accepted.status_code == 200
    assert accepted.json()["data"][0]["symbol"] == "BTCUSDT"
