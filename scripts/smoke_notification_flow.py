import asyncio

from mip_common.models import model_to_dict
from services.notification_service.app.repositories import InMemoryNotificationRepository
from services.notification_service.app.schemas import (
    NotificationMessage,
    NotificationPreference,
    NotificationSendRequest,
)
from services.notification_service.app.services import NotificationService


async def main() -> None:
    service = NotificationService(InMemoryNotificationRepository())
    delivered = await service.send(
        NotificationSendRequest(
            channel="console",
            userId="demo",
            message=NotificationMessage(
                title="Smart coin signal",
                body="BTCUSDT entered the opportunity bullish list.",
                severity="info",
                metadata={"symbol": "BTCUSDT", "list": "opportunity_bullish"},
            ),
        )
    )
    sse_delivery = await service.send(
        NotificationSendRequest(
            channel="sse",
            userId="demo",
            dedupeKey="signal:BTCUSDT:opportunity",
            message=NotificationMessage(
                title="SSE test",
                body="This delivery is published to active SSE subscribers.",
                severity="warning",
            ),
        )
    )
    deduped = await service.send(
        NotificationSendRequest(
            channel="sse",
            userId="demo",
            dedupeKey="signal:BTCUSDT:opportunity",
            message=NotificationMessage(
                title="SSE test",
                body="This delivery should be deduped.",
                severity="warning",
            ),
        )
    )
    preference = await service.save_preference(
        NotificationPreference(
            userId="demo",
            enabled=True,
            channels=["websocket"],
            minSeverity="warning",
            dedupeWindowSeconds=300,
        )
    )
    skipped = await service.send(
        NotificationSendRequest(
            channel="sse",
            userId="demo",
            message=NotificationMessage(
                title="Preference test",
                body="This delivery should be skipped by channel preference.",
                severity="warning",
            ),
        )
    )
    dead_letter = await service.send(
        NotificationSendRequest(
            channel="websocket",
            userId="demo",
            maxAttempts=2,
            message=NotificationMessage(
                title="WebSocket retry test",
                body="This delivery should enter dead_letter if WebSocket service is unavailable.",
                severity="error",
            ),
        )
    )
    history = await service.history("demo")
    print(model_to_dict(delivered))
    print(model_to_dict(sse_delivery))
    print(model_to_dict(deduped))
    print(model_to_dict(preference))
    print(model_to_dict(skipped))
    print(model_to_dict(dead_letter))
    print([model_to_dict(item) for item in history])


if __name__ == "__main__":
    asyncio.run(main())
