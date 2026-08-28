import os
from functools import lru_cache

from .services import HistoryService
from .sources import HttpHistorySource


@lru_cache
def get_history_service() -> HistoryService:
    return HistoryService(
        source=HttpHistorySource(),
        market_service_url=os.getenv("MARKET_SERVICE_URL", "http://localhost:8001"),
        feature_service_url=os.getenv("FEATURE_SERVICE_URL", "http://localhost:8003"),
        signal_service_url=os.getenv("SIGNAL_SERVICE_URL", "http://localhost:8005"),
        data_platform_url=os.getenv("DATA_PLATFORM_URL", "http://localhost:8011"),
    )
