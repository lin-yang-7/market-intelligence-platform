from fastapi.testclient import TestClient
from services.score_service.app.dependencies import get_score_service
from services.score_service.app.main import app
from services.score_service.app.services import ScoreService


def test_score_calculate_overall_returns_rule_score() -> None:
    app.dependency_overrides[get_score_service] = lambda: ScoreService()
    try:
        response = TestClient(app).post(
            "/v1/score/calculate",
            json={
                "symbol": "BTCUSDT",
                "exchange": "binance",
                "scoreType": "overall",
                "factors": {
                    "long_inflow_score": 90,
                    "price_momentum": 3,
                    "volume_activity": 80,
                },
            },
            headers={"X-Request-ID": "score-overall"},
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["requestId"] == "score-overall"
    assert payload["data"]["score"] == 70
    assert payload["data"]["confidence"] == 1
    assert [item["factor"] for item in payload["data"]["contributions"]] == [
        "long_inflow_score",
        "price_momentum",
        "volume_activity",
    ]


def test_score_calculate_single_factor_and_invalid_type() -> None:
    client = TestClient(app)
    app.dependency_overrides[get_score_service] = lambda: ScoreService()
    try:
        momentum = client.post(
            "/v1/score/calculate",
            json={
                "symbol": "ETHUSDT",
                "scoreType": "momentum",
                "factors": {"price_momentum": 4.2},
            },
        )
        invalid = client.post(
            "/v1/score/calculate",
            json={"symbol": "ETHUSDT", "scoreType": "unknown", "factors": {}},
        )
    finally:
        app.dependency_overrides.clear()

    assert momentum.status_code == 200
    assert momentum.json()["data"]["score"] == 42
    assert invalid.status_code == 400
    assert invalid.json()["code"] == 7001


def test_score_batch_returns_all_items() -> None:
    app.dependency_overrides[get_score_service] = lambda: ScoreService()
    try:
        response = TestClient(app).post(
            "/v1/score/batch",
            json={
                "items": [
                    {
                        "symbol": "BTCUSDT",
                        "scoreType": "longInflow",
                        "factors": {"long_inflow_score": 88},
                    },
                    {
                        "symbol": "ETHUSDT",
                        "scoreType": "volume",
                        "factors": {"volume_activity": 76},
                    },
                ]
            },
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert [item["score"] for item in payload["data"]] == [88, 76]
