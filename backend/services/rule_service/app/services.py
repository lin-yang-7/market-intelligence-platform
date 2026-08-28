import hashlib
import operator
import re
from collections.abc import Callable
from typing import Any

from mip_common.models import model_copy_with_update
from mip_common.responses import ServiceError, now_ms

from .repositories import RuleRepository
from .schemas import Rule, RuleCreateRequest, RuleEvaluateRequest, RuleMatch, RuleUpdateRequest

SUPPORTED_SCOPES = {"signal", "ranking", "feature", "market"}
SUPPORTED_ACTIONS = {"notify", "tag", "suppress", "route"}
CONDITION_PATTERN = re.compile(r"^(>=|<=|>|<|==)\s*(-?\d+(?:\.\d+)?)$")
OPERATORS: dict[str, Callable[[float, float], bool]] = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
}


class RuleService:
    def __init__(self, repository: RuleRepository) -> None:
        self.repository = repository

    async def create(self, request: RuleCreateRequest) -> Rule:
        self._validate_scope(request.scope)
        self._validate_action(request.action)
        self._validate_conditions(request.conditions)
        timestamp = now_ms()
        rule = Rule(
            ruleId=self._id("rule", request.userId, request.scope, request.name, timestamp),
            userId=request.userId,
            name=request.name,
            scope=request.scope,
            target=request.target.upper() if request.target else None,
            conditions=request.conditions,
            action=request.action,
            enabled=request.enabled,
            status="active" if request.enabled else "disabled",
            createdAt=timestamp,
            updatedAt=timestamp,
        )
        await self.repository.save_rule(rule)
        return rule

    async def list_rules(
        self,
        user_id: str | None = None,
        scope: str | None = None,
    ) -> list[Rule]:
        if scope:
            self._validate_scope(scope)
        return await self.repository.list_rules(user_id=user_id, scope=scope)

    async def update(self, request: RuleUpdateRequest) -> Rule:
        rule = await self.repository.get_rule(request.ruleId)
        if rule is None:
            raise ServiceError(7101, "Rule not found")
        conditions = request.conditions if request.conditions is not None else rule.conditions
        action = request.action if request.action is not None else rule.action
        self._validate_conditions(conditions)
        self._validate_action(action)
        enabled = rule.enabled if request.enabled is None else request.enabled
        updated = model_copy_with_update(
            rule,
            {
                "name": request.name or rule.name,
                "target": request.target.upper() if request.target else rule.target,
                "conditions": conditions,
                "action": action,
                "enabled": enabled,
                "status": "active" if enabled else "disabled",
                "updatedAt": now_ms(),
            },
        )
        await self.repository.save_rule(updated)
        return updated

    async def delete(self, rule_id: str) -> dict[str, str]:
        deleted = await self.repository.delete_rule(rule_id)
        if not deleted:
            raise ServiceError(7101, "Rule not found")
        return {"ruleId": rule_id, "status": "deleted"}

    async def evaluate(self, request: RuleEvaluateRequest) -> list[RuleMatch]:
        self._validate_scope(request.scope)
        rules = await self.repository.list_rules(user_id=request.userId, scope=request.scope)
        matches: list[RuleMatch] = []
        for rule in rules:
            if not rule.enabled:
                continue
            if request.target and rule.target and rule.target != request.target.upper():
                continue
            matched, reason = self._matches(rule.conditions, request.payload)
            if matched:
                matches.append(
                    RuleMatch(
                        ruleId=rule.ruleId,
                        name=rule.name,
                        action=rule.action,
                        matched=True,
                        reason=reason,
                        payload=request.payload,
                    )
                )
        return matches

    def _matches(self, conditions: dict[str, Any], payload: dict[str, Any]) -> tuple[bool, str]:
        for key, expected in conditions.items():
            if key not in payload:
                return False, f"missing {key}"
            actual = payload[key]
            if isinstance(expected, str) and CONDITION_PATTERN.match(expected.strip()):
                if not self._compare(float(actual), expected):
                    return False, f"{key} did not match {expected}"
                continue
            if actual != expected:
                return False, f"{key} did not equal {expected}"
        return True, "all conditions matched"

    def _validate_scope(self, scope: str) -> None:
        if scope not in SUPPORTED_SCOPES:
            raise ServiceError(7102, "Invalid rule scope")

    def _validate_action(self, action: str) -> None:
        if action not in SUPPORTED_ACTIONS:
            raise ServiceError(7103, "Invalid rule action")

    def _validate_conditions(self, conditions: dict[str, Any]) -> None:
        for value in conditions.values():
            if isinstance(value, str) and value[:1] in {">", "<", "="}:
                self._parse_condition(value)

    def _compare(self, actual: float, condition: str) -> bool:
        op, expected = self._parse_condition(condition)
        return OPERATORS[op](actual, expected)

    def _parse_condition(self, condition: str) -> tuple[str, float]:
        match = CONDITION_PATTERN.match(condition.strip())
        if match is None:
            raise ServiceError(7104, "Invalid rule condition")
        return match.group(1), float(match.group(2))

    @staticmethod
    def _id(prefix: str, *parts: object) -> str:
        raw = ":".join(str(part) for part in parts).encode()
        digest = hashlib.sha1(raw).hexdigest()[:12]
        return f"{prefix}_{digest}"
