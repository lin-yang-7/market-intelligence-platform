from functools import lru_cache

from mip_common.config import get_settings

from .repositories import InMemoryTickerRepository, MarketRepository, RedisTickerRepository
from .services import MarketService


@lru_cache
def get_repository() -> MarketRepository:
    settings = get_settings()
    if settings.repository_backend == "redis":
        import redis.asyncio as redis

        return RedisTickerRepository(redis.from_url(settings.redis_url, decode_responses=False))
    return InMemoryTickerRepository()


def get_market_service() -> MarketService:
    return MarketService(get_repository())
