from typing import Any

from pydantic import BaseModel, Field


class RuleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    scope: str = Field(default="signal", min_length=2, max_length=40)
    target: str | None = Field(default=None, min_length=2, max_length=80)
    conditions: dict[str, Any] = Field(default_factory=dict)
    action: str = Field(default="notify", min_length=2, max_length=40)
    userId: str = Field(default="default", min_length=1, max_length=80)
    enabled: bool = True


class RuleUpdateRequest(BaseModel):
    ruleId: str
    name: str | None = Field(default=None, min_length=1, max_length=120)
    target: str | None = Field(default=None, min_length=2, max_length=80)
    conditions: dict[str, Any] | None = None
    action: str | None = Field(default=None, min_length=2, max_length=40)
    enabled: bool | None = None


class Rule(BaseModel):
    ruleId: str
    userId: str
    name: str
    scope: str
    target: str | None = None
    conditions: dict[str, Any]
    action: str
    enabled: bool
    status: str
    createdAt: int
    updatedAt: int


class RuleEvaluateRequest(BaseModel):
    scope: str = Field(..., min_length=2, max_length=40)
    target: str | None = Field(default=None, min_length=2, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)
    userId: str | None = Field(default=None, min_length=1, max_length=80)


class RuleMatch(BaseModel):
    ruleId: str
    name: str
    action: str
    matched: bool
    reason: str
    payload: dict[str, Any]
