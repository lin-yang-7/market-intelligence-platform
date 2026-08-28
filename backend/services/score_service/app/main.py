from fastapi import Depends, FastAPI, Request
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .dependencies import get_score_service
from .schemas import ScoreBatchRequest, ScoreRequest
from .services import ScoreService

app = FastAPI(title="Score Service", version="0.1.0")
install_logging(app, "score-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "score-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/score/calculate")
async def calculate_score(
    payload: ScoreRequest,
    request: Request,
    service: ScoreService = Depends(get_score_service),
):
    return ok(await service.calculate(payload), request_id=request.state.request_id)


@app.post("/v1/score/batch")
async def batch_score(
    payload: ScoreBatchRequest,
    request: Request,
    service: ScoreService = Depends(get_score_service),
):
    return ok(await service.batch(payload), request_id=request.state.request_id)
