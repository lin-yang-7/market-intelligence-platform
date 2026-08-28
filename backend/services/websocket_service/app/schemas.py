from typing import Any

from pydantic import BaseModel, Field


class WebSocketEvent(BaseModel):
    event: str
    timestamp: int
    data: dict[str, Any] = Field(default_factory=dict)


class SubscribeMessage(BaseModel):
    action: str
    channels: list[str] = Field(default_factory=list)

