from typing import Any

from pydantic import BaseModel, Field


class AlertCreateRequest(BaseModel):
    type: str
    symbol: str | None = None
    conditions: dict[str, Any] = Field(default_factory=dict)
    channel: str = "sse"
    userId: str = "default"


class AlertUpdateRequest(BaseModel):
    alertId: str
    conditions: dict[str, Any] | None = None
    channel: str | None = None
    enabled: bool | None = None


class AlertRule(BaseModel):
    alertId: str
    userId: str
    type: str
    symbol: str | None = None
    conditions: dict[str, Any]
    channel: str
    enabled: bool = True
    status: str = "active"
    createdAt: int
    updatedAt: int


class AlertCreateResponse(BaseModel):
    alertId: str
    status: str


class AlertHistoryItem(BaseModel):
    historyId: str
    alertId: str
    symbol: str
    type: str
    channel: str
    triggerTime: int
    result: str
    signalId: str | None = None
    reason: str
