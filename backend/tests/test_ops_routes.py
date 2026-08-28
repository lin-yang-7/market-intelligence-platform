from fastapi import FastAPI
from fastapi.testclient import TestClient
from mip_common.ops import install_ops_routes
from services.market_service.app.main import app as market_app


def test_install_ops_routes_exposes_ready_and_metrics() -> None:
    app = FastAPI()
    install_ops_routes(app, "test-service")
    client = TestClient(app)

    ready = client.get("/ready").json()
    metrics = client.get("/metrics")

    assert ready["status"] == "ready"
    assert ready["service"] == "test-service"
    assert "mip_service_up" in metrics.text
    assert 'service="test-service"' in metrics.text


def test_market_service_exposes_ops_routes() -> None:
    client = TestClient(market_app)

    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").json()["status"] == "ready"
    assert "mip_service_uptime_seconds" in client.get("/metrics").text
