from typing import Any

from pydantic import BaseModel, Field


class HistoryQuery(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=30)
    exchange: str | None = Field(default=None, min_length=2, max_length=30)
    interval: str = Field(default="1m", min_length=1, max_length=10)
    features: list[str] = Field(default_factory=list)
    signalType: str | None = Field(default=None, min_length=2, max_length=30)
    startTime: int | None = Field(default=None, ge=0)
    endTime: int | None = Field(default=None, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class HistorySeries(BaseModel):
    name: str
    type: str
    points: list[dict[str, Any]]


class TimelineEvent(BaseModel):
    timestamp: int
    source: str
    symbol: str
    type: str
    title: str
    payload: dict[str, Any]


class RankingMonitorHistoryEvent(BaseModel):
    exchange: str
    symbol: str
    rankingType: str
    eventAction: str
    fromRank: int = 0
    toRank: int = 0
    score: float = 0.0
    previousScore: float = 0.0
    scoreChange: float = 0.0
    marketBias: str = ""
    summary: dict[str, Any] = Field(default_factory=dict)
    timestamp: int


class HistorySnapshot(BaseModel):
    symbol: str
    exchange: str | None = None
    interval: str
    series: list[HistorySeries]
    timeline: list[TimelineEvent]
