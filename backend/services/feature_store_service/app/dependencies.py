from functools import lru_cache

from .repositories import InMemoryFeatureStoreRepository
from .services import FeatureStoreService


@lru_cache
def get_repository() -> InMemoryFeatureStoreRepository:
    return InMemoryFeatureStoreRepository()


def get_feature_store_service() -> FeatureStoreService:
    return FeatureStoreService(get_repository())
