from fastapi import Depends, FastAPI, Request
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .dependencies import get_screener_service
from .schemas import CustomScreenerRequest, LongInflowScreenerRequest, ScreenerQueryRequest
from .services import ScreenerService

app = FastAPI(title="Screener Service", version="0.1.0")
install_logging(app, "screener-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "screener-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/screener/list")
async def list_screeners(
    request: Request,
    service: ScreenerService = Depends(get_screener_service),
):
    return ok(service.list_presets(), request_id=request.state.request_id)


@app.post("/v1/screener/query")
async def query_screener(
    request: Request,
    payload: ScreenerQueryRequest,
    service: ScreenerService = Depends(get_screener_service),
):
    results = await service.query(payload)
    return ok(results, request_id=request.state.request_id)


@app.post("/v1/screener/longInflow")
async def long_inflow_screener(
    request: Request,
    payload: LongInflowScreenerRequest,
    service: ScreenerService = Depends(get_screener_service),
):
    results = await service.long_inflow(payload)
    return ok(results, request_id=request.state.request_id)


@app.post("/v1/screener/custom")
async def custom_screener(
    request: Request,
    payload: CustomScreenerRequest,
    service: ScreenerService = Depends(get_screener_service),
):
    results = await service.custom(payload)
    return ok(results, request_id=request.state.request_id)
