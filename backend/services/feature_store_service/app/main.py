from fastapi import Depends, FastAPI, Query, Request
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .dependencies import get_feature_store_service
from .schemas import FeatureDefinitionRequest, FeatureValueWrite
from .services import FeatureStoreService

app = FastAPI(title="Feature Store Service", version="0.1.0")
install_logging(app, "feature-store-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "feature-store-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/feature-store/registry")
async def register_feature(
    payload: FeatureDefinitionRequest,
    request: Request,
    service: FeatureStoreService = Depends(get_feature_store_service),
):
    return ok(await service.register(payload), request_id=request.state.request_id)


@app.get("/v1/feature-store/catalog")
async def feature_catalog(
    request: Request,
    category: str | None = Query(default=None, min_length=2, max_length=80),
    status: str | None = Query(default="active", min_length=2, max_length=40),
    service: FeatureStoreService = Depends(get_feature_store_service),
):
    definitions = await service.list_definitions(category=category, status=status)
    return ok(definitions, request_id=request.state.request_id)


@app.get("/v1/feature-store/meta")
async def feature_meta(
    request: Request,
    feature: str = Query(..., min_length=2, max_length=80),
    version: str | None = Query(default=None, min_length=1, max_length=32),
    service: FeatureStoreService = Depends(get_feature_store_service),
):
    return ok(await service.get_definition(feature, version), request_id=request.state.request_id)


@app.post("/v1/feature-store/value")
async def write_feature_value(
    payload: FeatureValueWrite,
    request: Request,
    service: FeatureStoreService = Depends(get_feature_store_service),
):
    return ok(await service.write_value(payload), request_id=request.state.request_id)


@app.get("/v1/feature-store/latest")
async def latest_feature(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    feature: str = Query(..., min_length=2, max_length=80),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    service: FeatureStoreService = Depends(get_feature_store_service),
):
    return ok(await service.latest(symbol, feature, exchange), request_id=request.state.request_id)


@app.get("/v1/feature-store/history")
async def feature_history(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    feature: str = Query(..., min_length=2, max_length=80),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    limit: int = Query(default=100, ge=1, le=1000),
    service: FeatureStoreService = Depends(get_feature_store_service),
):
    history = await service.history(symbol, feature, exchange, limit)
    return ok(history, request_id=request.state.request_id)


@app.get("/v1/feature-store/materialize")
async def materialize_features(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    features: str = Query(..., min_length=2),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    service: FeatureStoreService = Depends(get_feature_store_service),
):
    feature_names = [feature.strip() for feature in features.split(",") if feature.strip()]
    return ok(
        await service.materialize(symbol, feature_names, exchange),
        request_id=request.state.request_id,
    )


@app.delete("/v1/feature-store/registry")
async def disable_feature(
    request: Request,
    feature: str = Query(..., min_length=2, max_length=80),
    version: str | None = Query(default=None, min_length=1, max_length=32),
    service: FeatureStoreService = Depends(get_feature_store_service),
):
    definition = await service.disable_definition(feature, version)
    return ok(definition, request_id=request.state.request_id)
