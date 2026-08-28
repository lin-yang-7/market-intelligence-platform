import asyncio
import json
from collections.abc import AsyncIterator

from mip_common.models import model_to_dict

from .schemas import NotificationDelivery


class SseNotificationBroker:
    def __init__(self) -> None:
        self.subscribers: set[asyncio.Queue[NotificationDelivery]] = set()

    async def publish(self, delivery: NotificationDelivery) -> int:
        delivered = 0
        for queue in list(self.subscribers):
            await queue.put(delivery)
            delivered += 1
        return delivered

    async def subscribe(self) -> AsyncIterator[str]:
        queue: asyncio.Queue[NotificationDelivery] = asyncio.Queue(maxsize=100)
        self.subscribers.add(queue)
        try:
            while True:
                delivery = await queue.get()
                payload = json.dumps(model_to_dict(delivery), separators=(",", ":"))
                yield f"event: notification.sent\ndata: {payload}\n\n"
        finally:
            self.subscribers.discard(queue)


sse_broker = SseNotificationBroker()
