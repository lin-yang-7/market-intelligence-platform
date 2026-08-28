from functools import lru_cache

from .repositories import InMemoryUserRepository, UserRepository
from .services import UserService


@lru_cache
def get_repository() -> UserRepository:
    return InMemoryUserRepository()


def get_user_service() -> UserService:
    return UserService(get_repository())
