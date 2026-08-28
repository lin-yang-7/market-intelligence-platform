from typing import Any

from pydantic import BaseModel, Field


class PipelineEvent(BaseModel):
    event_type: str = Field(..., min_length=3, max_length=64)
    timestamp: int = Field(..., ge=0)
    source: str = Field(..., min_length=2, max_length=64)
    data: dict[str, Any]


class QualityIssue(BaseModel):
    code: str
    severity: str
    message: str


class QualityReport(BaseModel):
    accepted: bool
    issue_count: int
    issues: list[QualityIssue]
    missing_rate: float
    delay_ms: int


class DataQualityReportBucket(BaseModel):
    eventType: str
    totalEvents: int
    acceptedEvents: int
    rejectedEvents: int
    warningEvents: int
    errorEvents: int
    avgMissingRate: float
    avgDelayMs: int
    maxDelayMs: int


class DataQualityReportRequest(BaseModel):
    events: list[PipelineEvent] = Field(..., min_length=1, max_length=1000)


class DataQualityReportResponse(BaseModel):
    totalEvents: int
    acceptedEvents: int
    rejectedEvents: int
    warningEvents: int
    errorEvents: int
    avgMissingRate: float
    avgDelayMs: int
    maxDelayMs: int
    buckets: list[DataQualityReportBucket]


class RoutePlan(BaseModel):
    event_type: str
    target_table: str
    storage: str
    partition_key: str
    dedupe_key: str


class ProcessedEvent(BaseModel):
    event: PipelineEvent
    quality: QualityReport
    route: RoutePlan
    normalized_data: dict[str, Any]


class StorageResult(BaseModel):
    stored: bool
    storage: str
    target_table: str
    row_count: int
    reason: str | None = None


class IngestResult(BaseModel):
    processed: ProcessedEvent
    storage: StorageResult


class StreamProcessingRequest(BaseModel):
    events: list[PipelineEvent] = Field(..., min_length=1, max_length=5000)
    windowMs: int = Field(default=60_000, ge=1000, le=86_400_000)


class StreamWindowResult(BaseModel):
    eventType: str
    symbol: str
    windowStart: int
    windowEnd: int
    eventCount: int
    minPrice: float = 0.0
    maxPrice: float = 0.0
    avgPrice: float = 0.0
    totalVolume: float = 0.0
    acceptedEvents: int
    rejectedEvents: int


class BatchPipelineRequest(BaseModel):
    events: list[PipelineEvent] = Field(..., min_length=1, max_length=10000)
    jobName: str = Field(default="daily_feature_rollup", min_length=3, max_length=80)


class BatchPipelineResult(BaseModel):
    jobName: str
    inputEvents: int
    outputRows: int
    symbols: list[str]
    featureRows: list[dict[str, Any]]


class WarehouseLayer(BaseModel):
    name: str
    purpose: str
    tables: list[str]
    inputEvents: int
    outputRows: int


class WarehousePlanRequest(BaseModel):
    events: list[PipelineEvent] = Field(..., min_length=1, max_length=10000)


class WarehousePlan(BaseModel):
    layers: list[WarehouseLayer]


class DataLakeWriteRequest(BaseModel):
    events: list[PipelineEvent] = Field(..., min_length=1, max_length=10000)
    dataset: str = Field(default="raw_events", min_length=3, max_length=80)


class DataLakeManifest(BaseModel):
    dataset: str
    root: str
    files: list[str]
    rowCount: int
    partitions: list[str]


class DataFreshnessRequest(BaseModel):
    events: list[PipelineEvent] = Field(..., min_length=1, max_length=10000)
    expectedSymbols: list[str] = Field(default_factory=list)
    maxDelayMs: int = Field(default=300_000, ge=1000)
    expectedIntervalMs: int = Field(default=60_000, ge=1000)


class DataFreshnessReport(BaseModel):
    totalEvents: int
    staleEvents: int
    missingSymbols: list[str]
    maxDelayMs: int
    eventLossSuspicions: list[dict[str, Any]]
    status: str


class LineageRequest(BaseModel):
    events: list[PipelineEvent] = Field(..., min_length=1, max_length=10000)


class LineageNode(BaseModel):
    id: str
    type: str
    label: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class LineageEdge(BaseModel):
    source: str
    target: str
    relation: str


class GovernanceReport(BaseModel):
    owners: dict[str, str]
    classifications: dict[str, str]
    lifecycle: dict[str, str]
    nodes: list[LineageNode]
    edges: list[LineageEdge]


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
