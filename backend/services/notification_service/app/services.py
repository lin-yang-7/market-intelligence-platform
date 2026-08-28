import hashlib

import httpx
from mip_common.config import get_settings
from mip_common.models import model_copy_with_update
from mip_common.responses import ServiceError, now_ms

from .broker import sse_broker
from .repositories import NotificationRepository
from .schemas import (
    NotificationChannel,
    NotificationDelivery,
    NotificationPreference,
    NotificationSendRequest,
)

SUPPORTED_CHANNELS = {"console", "sse", "websocket"}
SEVERITY_ORDER = {"debug": 0, "info": 1, "warning": 2, "error": 3, "critical": 4}


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    async def send(self, request: NotificationSendRequest) -> NotificationDelivery:
        if request.channel not in SUPPORTED_CHANNELS:
            raise ServiceError(8002, "Unsupported notification channel")
        timestamp = now_ms()
        delivery = NotificationDelivery(
            deliveryId=self._id(
                request.userId,
                request.channel,
                request.dedupeKey or "",
                request.message.title,
                request.message.body,
                timestamp,
            ),
            userId=request.userId,
            channel=request.channel,
            target=request.target,
            dedupeKey=request.dedupeKey,
            title=request.message.title,
            status="pending",
            createdAt=timestamp,
        )
        preference = await self.preference(request.userId)
        skipped = self._preference_skip(request, delivery, preference)
        if skipped:
            await self.repository.save(skipped)
            return skipped

        duplicate = await self._duplicate(request, delivery, preference)
        if duplicate:
            await self.repository.save(duplicate)
            return duplicate

        last_error: str | None = None
        for attempt in range(1, request.maxAttempts + 1):
            try:
                await self._deliver(request, delivery)
                delivered = model_copy_with_update(
                    delivery,
                    {
                        "status": "delivered",
                        "attempts": attempt,
                        "deliveredAt": now_ms(),
                    },
                )
                await self.repository.save(delivered)
                return delivered
            except Exception as exc:
                last_error = str(exc)

        dead_letter = model_copy_with_update(
            delivery,
            {
                "status": "dead_letter",
                "error": last_error,
                "attempts": request.maxAttempts,
                "deliveredAt": now_ms(),
            },
        )
        await self.repository.save(dead_letter)
        return dead_letter

    async def _deliver(
        self,
        request: NotificationSendRequest,
        delivery: NotificationDelivery,
    ) -> None:
        if request.channel == "console":
            print(f"[{request.message.severity}] {request.message.title}: {request.message.body}")
            return
        if request.channel == "sse":
            await sse_broker.publish(delivery)
            return
        if request.channel == "websocket":
            settings = get_settings()
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    f"{settings.websocket_service_url.rstrip('/')}/v1/ws/publish",
                    json={
                        "event": "notification.sent",
                        "timestamp": now_ms(),
                        "data": {
                            "userId": request.userId,
                            "title": request.message.title,
                            "body": request.message.body,
                            "severity": request.message.severity,
                            "metadata": request.message.metadata,
                        },
                    },
                )
                response.raise_for_status()
            return
        raise ServiceError(8002, "Unsupported notification channel")

    async def history(
        self,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[NotificationDelivery]:
        return await self.repository.list_deliveries(user_id, limit)

    async def preference(self, user_id: str) -> NotificationPreference:
        preference = await self.repository.get_preference(user_id)
        return preference or NotificationPreference(userId=user_id)

    async def save_preference(self, preference: NotificationPreference) -> NotificationPreference:
        invalid = [channel for channel in preference.channels if channel not in SUPPORTED_CHANNELS]
        if invalid:
            raise ServiceError(8002, "Unsupported notification channel")
        if preference.minSeverity not in SEVERITY_ORDER:
            raise ServiceError(8003, "Invalid notification preference")
        await self.repository.save_preference(preference)
        return preference

    def channels(self) -> list[NotificationChannel]:
        settings = get_settings()
        return [
            NotificationChannel(channel="console", enabled=True, targetRequired=False),
            NotificationChannel(
                channel="sse",
                enabled=True,
                targetRequired=False,
            ),
            NotificationChannel(
                channel="websocket",
                enabled=bool(settings.websocket_service_url),
                targetRequired=False,
            ),
        ]

    def _preference_skip(
        self,
        request: NotificationSendRequest,
        delivery: NotificationDelivery,
        preference: NotificationPreference,
    ) -> NotificationDelivery | None:
        if request.channel == "console":
            return None
        if not preference.enabled:
            return self._skipped(delivery, "user notifications disabled")
        if request.channel not in preference.channels:
            return self._skipped(delivery, "channel disabled by user preference")
        actual = SEVERITY_ORDER.get(request.message.severity, SEVERITY_ORDER["info"])
        minimum = SEVERITY_ORDER[preference.minSeverity]
        if actual < minimum:
            return self._skipped(delivery, "severity below user preference")
        return None

    async def _duplicate(
        self,
        request: NotificationSendRequest,
        delivery: NotificationDelivery,
        preference: NotificationPreference,
    ) -> NotificationDelivery | None:
        if not request.dedupeKey or preference.dedupeWindowSeconds <= 0:
            return None
        since = delivery.createdAt - preference.dedupeWindowSeconds * 1000
        recent = await self.repository.find_recent(
            request.userId,
            request.channel,
            request.dedupeKey,
            since,
        )
        if recent is None:
            return None
        return self._skipped(delivery, f"deduped by {recent.deliveryId}")

    def _skipped(self, delivery: NotificationDelivery, reason: str) -> NotificationDelivery:
        return model_copy_with_update(
            delivery,
            {
                "status": "skipped",
                "error": reason,
                "attempts": 0,
                "deliveredAt": now_ms(),
            },
        )

    @staticmethod
    def _id(*parts: object) -> str:
        raw = ":".join(str(part) for part in parts).encode()
        digest = hashlib.sha1(raw).hexdigest()[:12]
        return f"ntf_{digest}"
