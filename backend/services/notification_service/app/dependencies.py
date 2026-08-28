from functools import lru_cache

from .repositories import InMemoryNotificationRepository, NotificationRepository
from .services import NotificationService


@lru_cache
def get_repository() -> NotificationRepository:
    return InMemoryNotificationRepository()


def get_notification_service() -> NotificationService:
    return NotificationService(get_repository())
