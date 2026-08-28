from pydantic import BaseModel, Field


class FeatureDefinitionRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    category: str = Field(..., min_length=2, max_length=80)
    version: str = Field(default="v1", min_length=1, max_length=32)
    description: str = Field(default="", max_length=500)
    formula: str = Field(default="", max_length=1000)
    dataSource: str = Field(default="feature-service", min_length=2, max_length=120)
    updateFrequency: str = Field(default="realtime", min_length=2, max_length=80)
    owner: str = Field(default="system", min_length=1, max_length=80)
    dependencies: list[str] = Field(default_factory=list)


class FeatureDefinitionRecord(FeatureDefinitionRequest):
    featureId: str
    status: str = "active"
    createdAt: int
    updatedAt: int


class FeatureValueWrite(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=30)
    exchange: str = Field(default="binance", min_length=2, max_length=30)
    feature: str = Field(..., min_length=2, max_length=80)
    value: float
    version: str = Field(default="v1", min_length=1, max_length=32)
    timestamp: int = Field(..., ge=0)


class FeatureValueRecord(FeatureValueWrite):
    featureId: str | None = None
    storedAt: int


class MaterializedFeatureSet(BaseModel):
    symbol: str
    exchange: str
    features: dict[str, float]
    versions: dict[str, str]
    timestamp: int
