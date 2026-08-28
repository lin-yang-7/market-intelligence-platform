from functools import lru_cache

from services.notification_service.app.dependencies import get_notification_service

from .repositories import AlertRepository, InMemoryAlertRepository
from .services import AlertService


@lru_cache
def get_repository() -> AlertRepository:
    return InMemoryAlertRepository()


def get_alert_service() -> AlertService:
    return AlertService(get_repository(), get_notification_service())
