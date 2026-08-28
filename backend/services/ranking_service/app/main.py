from fastapi import Depends, FastAPI, Query, Request
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .dependencies import get_ranking_service
from .services import RankingService

app = FastAPI(title="Ranking Service", version="0.1.0")
install_logging(app, "ranking-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "ranking-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/ranking/overall")
async def overall_ranking(
    request: Request,
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    limit: int = Query(default=50, ge=1, le=100),
    service: RankingService = Depends(get_ranking_service),
):
    ranking = await service.get_ranking("overall", exchange=exchange, limit=limit)
    return ok(ranking, request_id=request.state.request_id)


@app.get("/v1/ranking/longInflow")
async def long_inflow_ranking(
    request: Request,
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    limit: int = Query(default=50, ge=1, le=100),
    service: RankingService = Depends(get_ranking_service),
):
    ranking = await service.get_ranking("longInflow", exchange=exchange, limit=limit)
    return ok(ranking, request_id=request.state.request_id)


@app.get("/v1/ranking/momentum")
async def momentum_ranking(
    request: Request,
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    limit: int = Query(default=50, ge=1, le=100),
    service: RankingService = Depends(get_ranking_service),
):
    ranking = await service.get_ranking("momentum", exchange=exchange, limit=limit)
    return ok(ranking, request_id=request.state.request_id)


@app.get("/v1/ranking/volume")
async def volume_ranking(
    request: Request,
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    limit: int = Query(default=50, ge=1, le=100),
    service: RankingService = Depends(get_ranking_service),
):
    ranking = await service.get_ranking("volume", exchange=exchange, limit=limit)
    return ok(ranking, request_id=request.state.request_id)


@app.post("/v1/ranking/monitor/{ranking_type}")
async def monitor_ranking(
    ranking_type: str,
    request: Request,
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    limit: int = Query(default=50, ge=1, le=100),
    min_score: float | None = Query(default=None, ge=0, le=100),
    max_score: float | None = Query(default=None, ge=0, le=100),
    service: RankingService = Depends(get_ranking_service),
):
    snapshot = await service.monitor_ranking(
        ranking_type,
        exchange=exchange,
        limit=limit,
        min_score=min_score,
        max_score=max_score,
    )
    return ok(snapshot, request_id=request.state.request_id)
