from fastapi import Depends, FastAPI, Query, Request
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .dependencies import get_feature_service
from .services import FeatureService

app = FastAPI(title="Feature Service", version="0.1.0")
install_logging(app, "feature-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "feature-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/feature/list")
async def list_features(request: Request, service: FeatureService = Depends(get_feature_service)):
    return ok(service.list_definitions(), request_id=request.state.request_id)


@app.get("/v1/feature/meta")
async def get_feature_meta(
    request: Request,
    feature: str = Query(..., min_length=2, max_length=64),
    service: FeatureService = Depends(get_feature_service),
):
    return ok(service.get_definition(feature), request_id=request.state.request_id)


@app.get("/v1/feature/current")
async def get_current_feature(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    feature: str = Query(..., min_length=2, max_length=64),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    service: FeatureService = Depends(get_feature_service),
):
    value = await service.get_current_feature(symbol, feature, exchange)
    return ok(value, request_id=request.state.request_id)


@app.get("/v1/feature/batch")
async def get_feature_batch(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    features: str = Query(..., min_length=2),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    service: FeatureService = Depends(get_feature_service),
):
    batch = await service.get_batch(
        symbol=symbol,
        features=[feature.strip() for feature in features.split(",") if feature.strip()],
        exchange=exchange,
    )
    return ok(batch, request_id=request.state.request_id)


@app.get("/v1/feature/pressure-support")
async def pressure_support(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    service: FeatureService = Depends(get_feature_service),
):
    interpretation = await service.pressure_support(symbol=symbol, exchange=exchange)
    return ok(interpretation, request_id=request.state.request_id)


@app.get("/v1/feature/history")
async def get_feature_history(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    feature: str = Query(..., min_length=2, max_length=64),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    startTime: int | None = Query(default=None, ge=0),
    endTime: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: FeatureService = Depends(get_feature_service),
):
    history = await service.get_history(
        symbol=symbol,
        feature=feature,
        exchange=exchange,
        start_time=startTime,
        end_time=endTime,
        limit=limit,
    )
    return ok(history, request_id=request.state.request_id)
