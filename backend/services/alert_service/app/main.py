import hmac

from fastapi import Depends, FastAPI, Header, Query, Request
from mip_common.config import get_settings
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok
from services.signal_service.app.schemas import Signal

from .dependencies import get_alert_service
from .schemas import AlertCreateRequest, AlertUpdateRequest
from .services import AlertService

app = FastAPI(title="Alert Service", version="0.1.0")
install_logging(app, "alert-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "alert-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/internal/alerts/evaluate")
async def evaluate_signal_internal(
    payload: Signal,
    request: Request,
    x_internal_service_token: str | None = Header(default=None),
    service: AlertService = Depends(get_alert_service),
):
    """Evaluate alert rules from an internal signal producer only."""
    if not hmac.compare_digest(
        x_internal_service_token or "", get_settings().internal_service_token
    ):
        raise ServiceError(1001, "Invalid internal service token")
    return ok(await service.evaluate_signal(payload), request_id=request.state.request_id)


@app.post("/v1/alert/create")
async def create_alert(
    request: Request,
    payload: AlertCreateRequest,
    service: AlertService = Depends(get_alert_service),
):
    result = await service.create_rule(payload)
    return ok(result, request_id=request.state.request_id)


@app.get("/v1/alert/list")
async def list_alerts(
    request: Request,
    userId: str | None = Query(default=None, min_length=1, max_length=64),
    service: AlertService = Depends(get_alert_service),
):
    rules = await service.list_rules(userId)
    return ok(rules, request_id=request.state.request_id)


@app.post("/v1/alert/update")
async def update_alert(
    request: Request,
    payload: AlertUpdateRequest,
    service: AlertService = Depends(get_alert_service),
):
    rule = await service.update_rule(payload)
    return ok(rule, request_id=request.state.request_id)


@app.delete("/v1/alert/{alert_id}")
async def delete_alert(
    request: Request,
    alert_id: str,
    service: AlertService = Depends(get_alert_service),
):
    result = await service.delete_rule(alert_id)
    return ok(result, request_id=request.state.request_id)


@app.post("/v1/alert/longInflow")
async def create_long_inflow_alert(
    request: Request,
    conditions: dict,
    symbol: str | None = Query(default=None, min_length=3, max_length=30),
    channel: str = Query(default="sse", min_length=3, max_length=30),
    userId: str = Query(default="default", min_length=1, max_length=64),
    service: AlertService = Depends(get_alert_service),
):
    result = await service.create_long_inflow_rule(
        conditions=conditions,
        symbol=symbol,
        channel=channel,
        user_id=userId,
    )
    return ok(result, request_id=request.state.request_id)


@app.post("/v1/alert/signal")
async def create_signal_alert(
    request: Request,
    signalType: str = Query(..., min_length=2, max_length=30),
    minScore: float = Query(default=85, ge=0, le=100),
    channel: str = Query(default="sse", min_length=3, max_length=30),
    userId: str = Query(default="default", min_length=1, max_length=64),
    service: AlertService = Depends(get_alert_service),
):
    result = await service.create_signal_rule(
        signal_type=signalType,
        min_score=minScore,
        channel=channel,
        user_id=userId,
    )
    return ok(result, request_id=request.state.request_id)


@app.get("/v1/alert/history")
async def alert_history(
    request: Request,
    symbol: str | None = Query(default=None, min_length=3, max_length=30),
    limit: int = Query(default=100, ge=1, le=1000),
    service: AlertService = Depends(get_alert_service),
):
    history = await service.history(symbol=symbol, limit=limit)
    return ok(history, request_id=request.state.request_id)
