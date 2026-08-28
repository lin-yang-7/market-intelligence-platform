from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=30)
    exchange: str = Field(default="binance", min_length=2, max_length=30)
    scoreType: str = Field(default="overall", min_length=2, max_length=30)
    factors: dict[str, float] = Field(default_factory=dict)


class ScoreBatchRequest(BaseModel):
    items: list[ScoreRequest] = Field(..., min_length=1, max_length=500)


class FactorContribution(BaseModel):
    factor: str
    value: float
    weight: float
    contribution: float


class ScoreResult(BaseModel):
    symbol: str
    exchange: str
    scoreType: str
    score: float
    confidence: float
    factors: dict[str, float]
    contributions: list[FactorContribution]
    modelVersion: str | None = None
    opportunityScore: float | None = None
    riskScore: float | None = None
    riskWarning: str | None = None
