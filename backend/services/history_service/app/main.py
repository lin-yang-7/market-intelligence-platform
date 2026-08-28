from fastapi import Depends, FastAPI, Query, Request
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .dependencies import get_history_service
from .schemas import HistoryQuery
from .services import DEFAULT_FEATURES, HistoryService

app = FastAPI(title="History Service", version="0.1.0")
install_logging(app, "history-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "history-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/history/snapshot")
async def history_snapshot(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    interval: str = Query(default="1m", min_length=1, max_length=10),
    features: str | None = Query(default=None, min_length=2),
    signalType: str | None = Query(default=None, min_length=2, max_length=30),
    startTime: int | None = Query(default=None, ge=0),
    endTime: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: HistoryService = Depends(get_history_service),
):
    query = _query(symbol, exchange, interval, features, signalType, startTime, endTime, limit)
    return ok(await service.snapshot(query), request_id=request.state.request_id)


@app.get("/v1/history/timeline")
async def history_timeline(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    interval: str = Query(default="1m", min_length=1, max_length=10),
    features: str | None = Query(default=None, min_length=2),
    signalType: str | None = Query(default=None, min_length=2, max_length=30),
    startTime: int | None = Query(default=None, ge=0),
    endTime: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: HistoryService = Depends(get_history_service),
):
    query = _query(symbol, exchange, interval, features, signalType, startTime, endTime, limit)
    return ok(await service.timeline(query), request_id=request.state.request_id)


@app.get("/v1/history/ranking-monitor/events")
async def history_ranking_monitor_events(
    request: Request,
    rankingType: str | None = Query(default=None, min_length=3, max_length=64),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    symbol: str | None = Query(default=None, min_length=3, max_length=64),
    eventAction: str | None = Query(default=None, min_length=3, max_length=64),
    limit: int = Query(default=100, ge=1, le=500),
    service: HistoryService = Depends(get_history_service),
):
    return ok(
        await service.ranking_monitor_events(
            ranking_type=rankingType,
            exchange=exchange,
            symbol=symbol,
            event_action=eventAction,
            limit=limit,
        ),
        request_id=request.state.request_id,
    )


def _query(
    symbol: str,
    exchange: str | None,
    interval: str,
    features: str | None,
    signal_type: str | None,
    start_time: int | None,
    end_time: int | None,
    limit: int,
) -> HistoryQuery:
    return HistoryQuery(
        symbol=symbol,
        exchange=exchange,
        interval=interval,
        features=[item.strip() for item in (features or "").split(",") if item.strip()]
        or DEFAULT_FEATURES,
        signalType=signal_type,
        startTime=start_time,
        endTime=end_time,
        limit=limit,
    )
