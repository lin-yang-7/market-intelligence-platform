import json

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from mip_common.logging import install_logging
from mip_common.models import validate_model
from mip_common.ops import install_ops_routes

from .events import sample_event
from .manager import SUPPORTED_CHANNELS, ConnectionManager
from .schemas import SubscribeMessage, WebSocketEvent

app = FastAPI(title="WebSocket Service", version="0.1.0")
install_logging(app, "websocket-service")
manager = ConnectionManager()
install_ops_routes(app, "websocket-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/ws/publish")
async def publish_event(payload: WebSocketEvent, request: Request) -> dict[str, int | str]:
    delivered = await manager.broadcast(payload)
    return {
        "status": "ok",
        "delivered": delivered,
        "requestId": request.headers.get("X-Request-ID", ""),
    }


@app.websocket("/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json(
            {
                "event": "connected",
                "channels": sorted(SUPPORTED_CHANNELS),
            }
        )
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if "text" in message and message["text"] == "ping":
                await websocket.send_text("pong")
                continue
            if "text" in message:
                payload = json.loads(message["text"])
            elif "bytes" in message:
                payload = json.loads(message["bytes"].decode("utf-8"))
            else:
                payload = {}
            command = validate_model(SubscribeMessage, payload)
            if command.action == "subscribe":
                channels = await manager.subscribe(websocket, command.channels)
                for channel in channels:
                    await manager.send_event(websocket, sample_event(channel))
            elif command.action == "unsubscribe":
                await manager.unsubscribe(websocket, command.channels)
            else:
                await websocket.send_json(
                    {
                        "event": "error",
                        "code": 2001,
                        "message": "Unsupported action",
                    }
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
