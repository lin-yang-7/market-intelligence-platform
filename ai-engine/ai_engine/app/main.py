from fastapi import Depends, FastAPI, Request
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .schemas import PredictRequest
from .service import PredictionService, prediction_service

app = FastAPI(title="AI Engine", version="0.1.0")
install_logging(app, "ai-engine")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "ai-engine")


def get_prediction_service() -> PredictionService:
    return prediction_service


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/ai/model")
async def model_metadata(
    request: Request,
    service: PredictionService = Depends(get_prediction_service),
):
    return ok(service.metadata(), request_id=request.state.request_id)


@app.post("/v1/ai/predict")
async def predict(
    payload: PredictRequest,
    request: Request,
    service: PredictionService = Depends(get_prediction_service),
):
    return ok(service.predict(payload), request_id=request.state.request_id)


@app.post("/v1/ai/explain")
async def explain(
    payload: PredictRequest,
    request: Request,
    service: PredictionService = Depends(get_prediction_service),
):
    return ok(service.explain(payload), request_id=request.state.request_id)
