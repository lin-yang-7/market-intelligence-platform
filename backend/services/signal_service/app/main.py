import hmac

from fastapi import Depends, FastAPI, Header, Query, Request
from mip_common.config import get_settings
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .dependencies import get_signal_service
from .schemas import InternalSignalGenerateRequest
from .services import SignalService

app = FastAPI(title="Signal Service", version="0.1.0")
install_logging(app, "signal-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "signal-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/internal/signals/generate")
async def generate_signals_internal(
    payload: InternalSignalGenerateRequest,
    request: Request,
    x_internal_service_token: str | None = Header(default=None),
    service: SignalService = Depends(get_signal_service),
):
    """Generate signals only for a caller inside the Docker/Kubernetes network."""
    if not hmac.compare_digest(
        x_internal_service_token or "", get_settings().internal_service_token
    ):
        raise ServiceError(1001, "Invalid internal service token")
    signals = await service.generate_from_ranking(
        payload.rankingType, payload.ranking, payload.minScore
    )
    return ok(signals, request_id=request.state.request_id)


@app.get("/v1/signal/current")
async def current_signals(
    request: Request,
    symbol: str | None = Query(default=None, min_length=3, max_length=30),
    type: str | None = Query(default=None, min_length=2, max_length=30),
    limit: int = Query(default=50, ge=1, le=100),
    service: SignalService = Depends(get_signal_service),
):
    signals = await service.current(symbol=symbol, signal_type=type, limit=limit)
    return ok(signals, request_id=request.state.request_id)


@app.get("/v1/signal/longInflow")
async def long_inflow_signals(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    service: SignalService = Depends(get_signal_service),
):
    signals = await service.long_inflow(limit=limit)
    return ok(signals, request_id=request.state.request_id)


@app.get("/v1/signal/detail")
async def signal_detail(
    request: Request,
    signalId: str = Query(..., min_length=4, max_length=64),
    service: SignalService = Depends(get_signal_service),
):
    signal = await service.detail(signalId)
    return ok(signal, request_id=request.state.request_id)


@app.get("/v1/signal/history")
async def signal_history(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    type: str | None = Query(default=None, min_length=2, max_length=30),
    startTime: int | None = Query(default=None, ge=0),
    endTime: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: SignalService = Depends(get_signal_service),
):
    signals = await service.history(
        symbol=symbol,
        signal_type=type,
        start_time=startTime,
        end_time=endTime,
        limit=limit,
    )
    return ok(signals, request_id=request.state.request_id)
