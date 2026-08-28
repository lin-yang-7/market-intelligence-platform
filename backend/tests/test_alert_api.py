from fastapi.testclient import TestClient
from services.alert_service.app.dependencies import get_alert_service
from services.alert_service.app.main import app
from services.alert_service.app.repositories import InMemoryAlertRepository
from services.alert_service.app.services import AlertService


def test_alert_create_list_update_and_delete_endpoints() -> None:
    service = AlertService(InMemoryAlertRepository())
    app.dependency_overrides[get_alert_service] = lambda: service
    try:
        create_response = TestClient(app).post(
            "/v1/alert/create",
            json={
                "type": "longInflow",
                "symbol": "BTCUSDT",
                "conditions": {"score": ">=90"},
                "channel": "sse",
            },
            headers={"X-Request-ID": "alert-create"},
        )
        alert_id = create_response.json()["data"]["alertId"]
        list_response = TestClient(app).get("/v1/alert/list")
        update_response = TestClient(app).post(
            "/v1/alert/update",
            json={"alertId": alert_id, "enabled": False},
        )
        delete_response = TestClient(app).delete(f"/v1/alert/{alert_id}")
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert create_response.json()["requestId"] == "alert-create"
    assert list_response.json()["data"][0]["alertId"] == alert_id
    assert update_response.json()["data"]["enabled"] is False
    assert update_response.json()["data"]["status"] == "disabled"
    assert delete_response.json()["data"]["status"] == "deleted"


def test_alert_history_endpoint_returns_empty_list() -> None:
    service = AlertService(InMemoryAlertRepository())
    app.dependency_overrides[get_alert_service] = lambda: service
    try:
        response = TestClient(app).get("/v1/alert/history", params={"symbol": "BTCUSDT"})
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == 0
    assert payload["data"] == []


def test_internal_alert_evaluation_rejects_untrusted_caller() -> None:
    service = AlertService(InMemoryAlertRepository())
    app.dependency_overrides[get_alert_service] = lambda: service
    signal = {
        "signalId": "sig_internal_test",
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "type": "longInflow",
        "score": 90.0,
        "confidence": 0.9,
        "reasons": ["high_inflow"],
        "factors": {"long_inflow_score": 90.0},
        "explanation": "test",
        "timestamp": 1700000000000,
    }
    try:
        forbidden = TestClient(app).post("/internal/alerts/evaluate", json=signal)
        accepted = TestClient(app).post(
            "/internal/alerts/evaluate",
            headers={"X-Internal-Service-Token": "local-internal-service-token"},
            json=signal,
        )
    finally:
        app.dependency_overrides.clear()

    assert forbidden.status_code == 400
    assert accepted.status_code == 200
    assert accepted.json()["data"] == []
