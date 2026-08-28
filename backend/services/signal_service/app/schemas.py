from pydantic import BaseModel, Field
from services.ranking_service.app.schemas import RankingItem


class Signal(BaseModel):
    signalId: str
    symbol: str
    exchange: str
    type: str
    score: float
    confidence: float
    reasons: list[str]
    factors: dict[str, float]
    explanation: str
    timestamp: int = Field(description="Unix timestamp in milliseconds.")
    status: str = "active"
    modelVersion: str | None = None
    opportunityScore: float | None = None
    riskScore: float | None = None
    riskWarning: str | None = None


class InternalSignalGenerateRequest(BaseModel):
    """Trusted internal payload used by the automated ranking-to-signal worker."""

    rankingType: str
    ranking: list[RankingItem]
    minScore: float = Field(default=70.0, ge=0, le=100)
