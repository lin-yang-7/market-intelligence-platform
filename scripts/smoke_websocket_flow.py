from fastapi.testclient import TestClient
from mip_common.responses import now_ms
from services.websocket_service.app.main import app


def main() -> None:
    client = TestClient(app)
    with client.websocket_connect("/v1/ws") as websocket:
        print(websocket.receive_json())
        websocket.send_json(
            {
                "action": "subscribe",
                "channels": ["market.ticker", "signal.created", "notification.sent"],
            }
        )
        print(websocket.receive_json())
        print(websocket.receive_json())
        print(websocket.receive_json())
        print(websocket.receive_json())
        response = client.post(
            "/v1/ws/publish",
            json={
                "event": "notification.sent",
                "timestamp": now_ms(),
                "data": {"title": "Push test", "body": "WebSocket notification"},
            },
        )
        print(response.json())
        print(websocket.receive_json())
        websocket.send_text("ping")
        print(websocket.receive_text())


if __name__ == "__main__":
    main()
