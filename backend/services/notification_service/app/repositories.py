from typing import Protocol

from .schemas import NotificationDelivery, NotificationPreference


class NotificationRepository(Protocol):
    async def save(self, delivery: NotificationDelivery) -> None:
        ...

    async def list_deliveries(
        self,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[NotificationDelivery]:
        ...

    async def find_recent(
        self,
        user_id: str,
        channel: str,
        dedupe_key: str,
        since: int,
    ) -> NotificationDelivery | None:
        ...

    async def save_preference(self, preference: NotificationPreference) -> None:
        ...

    async def get_preference(self, user_id: str) -> NotificationPreference | None:
        ...


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self._deliveries: dict[str, NotificationDelivery] = {}
        self._preferences: dict[str, NotificationPreference] = {}

    async def save(self, delivery: NotificationDelivery) -> None:
        self._deliveries[delivery.deliveryId] = delivery

    async def list_deliveries(
        self,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[NotificationDelivery]:
        rows = list(self._deliveries.values())
        if user_id:
            rows = [row for row in rows if row.userId == user_id]
        rows.sort(key=lambda row: row.createdAt, reverse=True)
        return rows[: max(1, min(limit, 1000))]

    async def find_recent(
        self,
        user_id: str,
        channel: str,
        dedupe_key: str,
        since: int,
    ) -> NotificationDelivery | None:
        candidates = [
            row
            for row in self._deliveries.values()
            if row.userId == user_id
            and row.channel == channel
            and row.dedupeKey == dedupe_key
            and row.createdAt >= since
        ]
        candidates.sort(key=lambda row: row.createdAt, reverse=True)
        return candidates[0] if candidates else None

    async def save_preference(self, preference: NotificationPreference) -> None:
        self._preferences[preference.userId] = preference

    async def get_preference(self, user_id: str) -> NotificationPreference | None:
        return self._preferences.get(user_id)
