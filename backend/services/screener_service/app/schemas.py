from typing import Any

from pydantic import BaseModel, Field


class ScreenerPreset(BaseModel):
    id: str
    name: str
    type: str


class ScreenerCondition(BaseModel):
    feature: str
    operator: str
    value: Any


class ScreenerQueryRequest(BaseModel):
    type: str
    timeframe: str = "1h"
    exchange: str | None = None
    limit: int = Field(default=50, ge=1, le=100)
    minScore: float = Field(default=0.0, ge=0, le=100)


class LongInflowScreenerRequest(BaseModel):
    timeframe: str = "1h"
    exchange: str | None = None
    minScore: float = Field(default=70.0, ge=0, le=100)
    minVolume: float = Field(default=0.0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)


class CustomScreenerRequest(BaseModel):
    exchange: str | None = None
    conditions: list[ScreenerCondition]
    limit: int = Field(default=50, ge=1, le=100)


class ScreenerResult(BaseModel):
    symbol: str
    exchange: str
    score: float
    rank: int
    signals: list[str]
    timestamp: int
    factors: dict[str, float]

