from fastapi.testclient import TestClient
from services.feature_store_service.app.dependencies import get_feature_store_service
from services.feature_store_service.app.main import app
from services.feature_store_service.app.repositories import InMemoryFeatureStoreRepository
from services.feature_store_service.app.services import FeatureStoreService


def test_feature_store_catalog_bootstraps_default_definitions() -> None:
    service = FeatureStoreService(InMemoryFeatureStoreRepository())
    app.dependency_overrides[get_feature_store_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/v1/feature-store/catalog",
            headers={"X-Request-ID": "feature-store-catalog"},
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert payload["requestId"] == "feature-store-catalog"
    assert {item["name"] for item in payload["data"]} >= {
        "last_price",
        "price_momentum",
        "volume_activity",
        "long_inflow_score",
    }


def test_feature_store_write_latest_history_materialize_and_disable() -> None:
    service = FeatureStoreService(InMemoryFeatureStoreRepository())
    app.dependency_overrides[get_feature_store_service] = lambda: service
    client = TestClient(app)
    try:
        register = client.post(
            "/v1/feature-store/registry",
            json={
                "name": "custom_flow",
                "category": "capital_flow",
                "version": "v1",
                "description": "Custom flow score",
            },
        )
        write = client.post(
            "/v1/feature-store/value",
            json={
                "symbol": "BTCUSDT",
                "exchange": "binance",
                "feature": "custom_flow",
                "value": 88.5,
                "version": "v1",
                "timestamp": 1700000000000,
            },
        )
        latest = client.get(
            "/v1/feature-store/latest",
            params={"symbol": "BTCUSDT", "feature": "custom_flow", "exchange": "binance"},
        )
        history = client.get(
            "/v1/feature-store/history",
            params={"symbol": "BTCUSDT", "feature": "custom_flow"},
        )
        materialized = client.get(
            "/v1/feature-store/materialize",
            params={"symbol": "BTCUSDT", "features": "custom_flow"},
        )
        disabled = client.delete(
            "/v1/feature-store/registry",
            params={"feature": "custom_flow", "version": "v1"},
        )
    finally:
        app.dependency_overrides.clear()

    assert register.status_code == 200
    assert write.json()["data"]["featureId"] == register.json()["data"]["featureId"]
    assert latest.json()["data"]["value"] == 88.5
    assert history.json()["data"][0]["feature"] == "custom_flow"
    assert materialized.json()["data"]["features"] == {"custom_flow": 88.5}
    assert disabled.json()["data"]["status"] == "disabled"


def test_feature_store_missing_value_returns_error() -> None:
    service = FeatureStoreService(InMemoryFeatureStoreRepository())
    app.dependency_overrides[get_feature_store_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/v1/feature-store/latest",
            params={"symbol": "BTCUSDT", "feature": "missing_feature"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["code"] == 7202
