from fastapi import WebSocket
from mip_common.models import model_to_dict

from .schemas import WebSocketEvent

SUPPORTED_CHANNELS = {
    "market.ticker",
    "ranking.updated",
    "ranking.monitor.updated",
    "ranking.entered",
    "ranking.exited",
    "ranking.moved",
    "ranking.strategy",
    "signal.created",
    "alert.triggered",
    "notification.sent",
}


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()
        self.subscriptions: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.add(websocket)
        self.subscriptions[websocket] = set()

    def disconnect(self, websocket: WebSocket) -> None:
        self.active.discard(websocket)
        self.subscriptions.pop(websocket, None)

    async def subscribe(self, websocket: WebSocket, channels: list[str]) -> list[str]:
        valid = [channel for channel in channels if channel in SUPPORTED_CHANNELS]
        self.subscriptions.setdefault(websocket, set()).update(valid)
        await websocket.send_json({"event": "subscribed", "channels": valid})
        return valid

    async def unsubscribe(self, websocket: WebSocket, channels: list[str]) -> list[str]:
        current = self.subscriptions.setdefault(websocket, set())
        for channel in channels:
            current.discard(channel)
        await websocket.send_json({"event": "unsubscribed", "channels": channels})
        return channels

    async def send_event(self, websocket: WebSocket, event: WebSocketEvent) -> None:
        await websocket.send_json(model_to_dict(event))

    async def broadcast(self, event: WebSocketEvent) -> int:
        delivered = 0
        for websocket in list(self.active):
            if event.event in self.subscriptions.get(websocket, set()):
                await self.send_event(websocket, event)
                delivered += 1
        return delivered
