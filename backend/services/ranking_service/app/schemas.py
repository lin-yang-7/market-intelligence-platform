from typing import Any

from pydantic import BaseModel, Field


class RankingItem(BaseModel):
    rank: int
    symbol: str
    exchange: str
    score: float
    confidence: float
    timestamp: int = Field(description="Unix timestamp in milliseconds.")
    factors: dict[str, float]
    modelVersion: str | None = None
    opportunityScore: float | None = None
    riskScore: float | None = None
    riskWarning: str | None = None
    strategyState: str | None = None
    signalColor: str | None = None
    reasonTags: list[str] = Field(default_factory=list)
    guidance: str | None = None


class RankingEntered(BaseModel):
    symbol: str
    exchange: str
    toRank: int
    score: float
    item: RankingItem


class RankingExited(BaseModel):
    symbol: str
    exchange: str
    fromRank: int
    previousScore: float
    item: RankingItem


class RankingMoved(BaseModel):
    symbol: str
    exchange: str
    fromRank: int
    toRank: int
    previousScore: float
    score: float
    scoreChange: float
    item: RankingItem


class RankingStrategyEvent(BaseModel):
    event: str
    severity: str
    title: str
    body: str
    symbol: str | None = None
    item: RankingItem | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RankingMonitorChanges(BaseModel):
    entered: list[RankingEntered]
    exited: list[RankingExited]
    moved: list[RankingMoved]
    strategyEvents: list[RankingStrategyEvent] = Field(default_factory=list)


class RankingMonitorSnapshot(BaseModel):
    rankingType: str
    exchange: str | None = None
    updatedAt: int
    active: list[RankingItem]
    changes: RankingMonitorChanges
    summary: dict[str, Any] = Field(default_factory=dict)
