from fastapi import Depends, FastAPI, Query, Request
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .jobs import (
    BatchPipelineJob,
    DataFreshnessMonitor,
    GovernanceCatalog,
    LocalDataLake,
    StreamProcessingJob,
    WarehousePlanner,
)
from .processor import PipelineProcessor, pipeline_processor
from .schemas import (
    BatchPipelineRequest,
    DataFreshnessRequest,
    DataLakeWriteRequest,
    DataQualityReportRequest,
    IngestResult,
    LineageRequest,
    PipelineEvent,
    StreamProcessingRequest,
    WarehousePlanRequest,
)
from .storage import EventStorage, create_event_storage

app = FastAPI(title="Data Platform", version="0.1.0")
install_logging(app, "data-platform")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "data-platform")


def get_pipeline_processor() -> PipelineProcessor:
    return pipeline_processor


def get_event_storage() -> EventStorage:
    return create_event_storage()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/data/validate")
async def validate_event(
    payload: PipelineEvent,
    request: Request,
    processor: PipelineProcessor = Depends(get_pipeline_processor),
):
    return ok(processor.validate(payload), request_id=request.state.request_id)


@app.post("/v1/data/quality/report")
async def quality_report(
    payload: DataQualityReportRequest,
    request: Request,
    processor: PipelineProcessor = Depends(get_pipeline_processor),
):
    return ok(processor.quality_report(payload.events), request_id=request.state.request_id)


@app.post("/v1/data/stream/process")
async def stream_process(payload: StreamProcessingRequest, request: Request):
    result = StreamProcessingJob().run(payload.events, payload.windowMs)
    return ok(result, request_id=request.state.request_id)


@app.post("/v1/data/batch/run")
async def batch_run(payload: BatchPipelineRequest, request: Request):
    result = BatchPipelineJob().run(payload.events, payload.jobName)
    return ok(result, request_id=request.state.request_id)


@app.post("/v1/data/warehouse/plan")
async def warehouse_plan(payload: WarehousePlanRequest, request: Request):
    result = WarehousePlanner().plan(payload.events)
    return ok(result, request_id=request.state.request_id)


@app.post("/v1/data/lake/write")
async def lake_write(payload: DataLakeWriteRequest, request: Request):
    result = LocalDataLake().write(payload.events, payload.dataset)
    return ok(result, request_id=request.state.request_id)


@app.post("/v1/data/freshness/report")
async def freshness_report(payload: DataFreshnessRequest, request: Request):
    result = DataFreshnessMonitor().report(
        payload.events,
        expected_symbols=payload.expectedSymbols,
        max_delay_ms=payload.maxDelayMs,
        expected_interval_ms=payload.expectedIntervalMs,
    )
    return ok(result, request_id=request.state.request_id)


@app.post("/v1/data/governance/lineage")
async def governance_lineage(payload: LineageRequest, request: Request):
    result = GovernanceCatalog().report(payload.events)
    return ok(result, request_id=request.state.request_id)


@app.post("/v1/data/route")
async def route_event(
    payload: PipelineEvent,
    request: Request,
    processor: PipelineProcessor = Depends(get_pipeline_processor),
):
    return ok(processor.route(payload), request_id=request.state.request_id)


@app.post("/v1/data/process")
async def process_event(
    payload: PipelineEvent,
    request: Request,
    processor: PipelineProcessor = Depends(get_pipeline_processor),
):
    return ok(processor.process(payload), request_id=request.state.request_id)


@app.post("/v1/data/store")
async def store_event(
    payload: PipelineEvent,
    request: Request,
    processor: PipelineProcessor = Depends(get_pipeline_processor),
    storage: EventStorage = Depends(get_event_storage),
):
    processed = processor.process(payload)
    return ok(await storage.write(processed), request_id=request.state.request_id)


@app.post("/v1/data/ingest")
async def ingest_event(
    payload: PipelineEvent,
    request: Request,
    processor: PipelineProcessor = Depends(get_pipeline_processor),
    storage: EventStorage = Depends(get_event_storage),
):
    processed = processor.process(payload)
    stored = await storage.write(processed)
    return ok(
        IngestResult(processed=processed, storage=stored),
        request_id=request.state.request_id,
    )


@app.get("/v1/data/ranking-monitor/events")
async def ranking_monitor_events(
    request: Request,
    rankingType: str | None = Query(default=None, min_length=3, max_length=64),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    symbol: str | None = Query(default=None, min_length=3, max_length=64),
    eventAction: str | None = Query(default=None, min_length=3, max_length=64),
    limit: int = Query(default=100, ge=1, le=500),
    storage: EventStorage = Depends(get_event_storage),
):
    events = await storage.list_ranking_monitor_events(
        ranking_type=rankingType,
        exchange=exchange,
        symbol=symbol,
        event_action=eventAction,
        limit=limit,
    )
    return ok(events, request_id=request.state.request_id)
