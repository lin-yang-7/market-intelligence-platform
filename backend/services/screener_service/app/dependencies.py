from services.feature_service.app.dependencies import get_repository

from .services import ScreenerService


def get_screener_service() -> ScreenerService:
    return ScreenerService(get_repository())

