from pydantic import BaseModel, Field


class FeatureDefinition(BaseModel):
    name: str
    category: str
    version: str
    description: str
    updateInterval: str


class FeatureValue(BaseModel):
    symbol: str
    exchange: str
    feature: str
    value: float
    timestamp: int = Field(description="Unix timestamp in milliseconds.")
    version: str = "v1"


class FeatureBatchResponse(BaseModel):
    symbol: str
    exchange: str
    features: dict[str, float]
    timestamp: int


class PressureSupportInterpretation(BaseModel):
    symbol: str
    exchange: str
    price: float
    supportLevel: float
    resistanceLevel: float
    mainForceNetInflow: float
    mainForceRatio: float
    bias: str
    guidance: str
    timestamp: int
