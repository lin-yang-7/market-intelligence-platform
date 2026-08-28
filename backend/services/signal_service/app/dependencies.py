from functools import lru_cache

from mip_common.config import get_settings

from .repositories import InMemorySignalRepository, RedisSignalRepository, SignalRepository
from .services import SignalService


@lru_cache
def get_repository() -> SignalRepository:
    settings = get_settings()
    if settings.repository_backend == "redis":
        import redis.asyncio as redis

        return RedisSignalRepository(redis.from_url(settings.redis_url, decode_responses=False))
    return InMemorySignalRepository()


def get_signal_service() -> SignalService:
    return SignalService(get_repository())
