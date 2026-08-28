from fastapi import Depends, FastAPI, Query, Request
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .dependencies import get_rule_service
from .schemas import RuleCreateRequest, RuleEvaluateRequest, RuleUpdateRequest
from .services import RuleService

app = FastAPI(title="Rule Service", version="0.1.0")
install_logging(app, "rule-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "rule-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/rule/create")
async def create_rule(
    payload: RuleCreateRequest,
    request: Request,
    service: RuleService = Depends(get_rule_service),
):
    return ok(await service.create(payload), request_id=request.state.request_id)


@app.get("/v1/rule/list")
async def list_rules(
    request: Request,
    userId: str | None = Query(default=None, min_length=1, max_length=80),
    scope: str | None = Query(default=None, min_length=2, max_length=40),
    service: RuleService = Depends(get_rule_service),
):
    rules = await service.list_rules(user_id=userId, scope=scope)
    return ok(rules, request_id=request.state.request_id)


@app.post("/v1/rule/update")
async def update_rule(
    payload: RuleUpdateRequest,
    request: Request,
    service: RuleService = Depends(get_rule_service),
):
    return ok(await service.update(payload), request_id=request.state.request_id)


@app.delete("/v1/rule/{rule_id}")
async def delete_rule(
    rule_id: str,
    request: Request,
    service: RuleService = Depends(get_rule_service),
):
    return ok(await service.delete(rule_id), request_id=request.state.request_id)


@app.post("/v1/rule/evaluate")
async def evaluate_rule(
    payload: RuleEvaluateRequest,
    request: Request,
    service: RuleService = Depends(get_rule_service),
):
    return ok(await service.evaluate(payload), request_id=request.state.request_id)
