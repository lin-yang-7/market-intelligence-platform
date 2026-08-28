from typing import Protocol

from .schemas import Rule


class RuleRepository(Protocol):
    async def save_rule(self, rule: Rule) -> None:
        ...

    async def get_rule(self, rule_id: str) -> Rule | None:
        ...

    async def list_rules(
        self,
        user_id: str | None = None,
        scope: str | None = None,
    ) -> list[Rule]:
        ...

    async def delete_rule(self, rule_id: str) -> bool:
        ...


class InMemoryRuleRepository:
    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}

    async def save_rule(self, rule: Rule) -> None:
        self._rules[rule.ruleId] = rule

    async def get_rule(self, rule_id: str) -> Rule | None:
        return self._rules.get(rule_id)

    async def list_rules(
        self,
        user_id: str | None = None,
        scope: str | None = None,
    ) -> list[Rule]:
        rules = list(self._rules.values())
        if user_id:
            rules = [rule for rule in rules if rule.userId == user_id]
        if scope:
            rules = [rule for rule in rules if rule.scope == scope]
        rules.sort(key=lambda rule: rule.createdAt, reverse=True)
        return rules

    async def delete_rule(self, rule_id: str) -> bool:
        return self._rules.pop(rule_id, None) is not None
