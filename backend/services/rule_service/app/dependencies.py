from functools import lru_cache

from .repositories import InMemoryRuleRepository
from .services import RuleService


@lru_cache
def get_repository() -> InMemoryRuleRepository:
    return InMemoryRuleRepository()


def get_rule_service() -> RuleService:
    return RuleService(get_repository())
