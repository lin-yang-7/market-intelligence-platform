from functools import lru_cache

from mip_common.config import get_settings

from .repositories import FeatureRepository, InMemoryFeatureRepository, RedisFeatureRepository
from .services import FeatureService


@lru_cache
def get_repository() -> FeatureRepository:
    settings = get_settings()
    if settings.repository_backend == "redis":
        import redis.asyncio as redis

        return RedisFeatureRepository(redis.from_url(settings.redis_url, decode_responses=False))
    return InMemoryFeatureRepository()


def get_feature_service() -> FeatureService:
    return FeatureService(get_repository())
