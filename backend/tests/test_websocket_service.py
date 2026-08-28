from fastapi.testclient import TestClient
from services.websocket_service.app.main import app


def test_websocket_subscribe_receives_sample_event_and_pong() -> None:
    client = TestClient(app)
    with client.websocket_connect("/v1/ws") as websocket:
        connected = websocket.receive_json()
        assert connected["event"] == "connected"
        assert "market.ticker" in connected["channels"]
        assert "ranking.entered" in connected["channels"]

        websocket.send_json(
            {"action": "subscribe", "channels": ["market.ticker", "ranking.entered"]}
        )
        subscribed = websocket.receive_json()
        event = websocket.receive_json()
        assert subscribed == {
            "event": "subscribed",
            "channels": ["market.ticker", "ranking.entered"],
        }
        assert event["event"] == "market.ticker"
        assert event["data"]["symbol"] == "BTCUSDT"
        ranking_event = websocket.receive_json()
        assert ranking_event["event"] == "ranking.entered"
        assert ranking_event["data"]["symbol"] == "BTCUSDT"

        websocket.send_text("ping")
        assert websocket.receive_text() == "pong"


def test_websocket_rejects_unsupported_action() -> None:
    client = TestClient(app)
    with client.websocket_connect("/v1/ws") as websocket:
        websocket.receive_json()
        websocket.send_json({"action": "unknown", "channels": []})
        error = websocket.receive_json()
        assert error["event"] == "error"
        assert error["code"] == 2001
