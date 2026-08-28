from pydantic import BaseModel, Field


class FeatureVector(BaseModel):
    capital_flow: float = Field(..., ge=-1)
    volume_imbalance: float = Field(..., ge=-1, le=1)
    price_momentum: float = Field(..., ge=-1, le=1)
    volatility: float = Field(..., ge=0)
    liquidity: float = Field(..., ge=0)


class PredictRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=30)
    exchange: str = Field(default="binance", min_length=2, max_length=30)
    features: FeatureVector
    model_version: str | None = Field(default=None, min_length=2, max_length=64)


class FactorContribution(BaseModel):
    factor: str
    contribution: float
    direction: str


class PredictionResult(BaseModel):
    symbol: str
    exchange: str
    model_version: str
    opportunity_score: float
    risk_score: float
    confidence: float
    overall_score: float
    prediction: float
    factors: list[FactorContribution]
    risk_warning: str


class ModelMetadata(BaseModel):
    model_name: str
    model_version: str
    strategy: str
    weights: dict[str, float]
    supported_scenarios: list[str]
