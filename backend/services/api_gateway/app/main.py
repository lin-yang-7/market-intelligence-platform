import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mip_common.auth import ApiIdentity, get_api_identity
from mip_common.config import get_settings
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.rate_limit import FixedWindowRateLimiter
from mip_common.rbac import require_request_permission
from mip_common.responses import ServiceError, now_ms

app = FastAPI(title="API Gateway", version="0.1.0")
install_logging(app, "api-gateway")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "api-gateway")

MARKET_SERVICE_URL = os.getenv("MARKET_SERVICE_URL", "http://localhost:8001")
FEATURE_SERVICE_URL = os.getenv("FEATURE_SERVICE_URL", "http://localhost:8003")
FEATURE_STORE_SERVICE_URL = os.getenv("FEATURE_STORE_SERVICE_URL", "http://localhost:8016")
RANKING_SERVICE_URL = os.getenv("RANKING_SERVICE_URL", "http://localhost:8004")
SIGNAL_SERVICE_URL = os.getenv("SIGNAL_SERVICE_URL", "http://localhost:8005")
ALERT_SERVICE_URL = os.getenv("ALERT_SERVICE_URL", "http://localhost:8006")
RULE_SERVICE_URL = os.getenv("RULE_SERVICE_URL", "http://localhost:8015")
SCREENER_SERVICE_URL = os.getenv("SCREENER_SERVICE_URL", "http://localhost:8007")
HISTORY_SERVICE_URL = os.getenv("HISTORY_SERVICE_URL", "http://localhost:8009")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8010")
SCORE_SERVICE_URL = os.getenv("SCORE_SERVICE_URL", "http://localhost:8014")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8012")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8013")
rate_limiter = FixedWindowRateLimiter()


@app.middleware("http")
async def resolve_dynamic_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if api_key:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(
                    f"{USER_SERVICE_URL}/internal/api-keys/verify",
                    headers={
                        "X-API-Key": api_key,
                        "X-Internal-Service-Token": settings.internal_service_token,
                    },
                )
        except httpx.HTTPError:
            return _gateway_error(request, 503, 5001, "Authentication service unavailable")
        if response.status_code != 200:
            return _gateway_error(request, 401, 1001, "Invalid API Key")
        payload = response.json().get("data", {})
        request.state.api_identity = ApiIdentity(
            principal=f"api-key:{payload['keyId']}",
            plan=str(payload["plan"]),
            authenticated=True,
            # API keys receive only their verified scopes; they never inherit
            # the owner's broad interactive-user role.
            role="api_key",
            scopes=frozenset(str(scope) for scope in payload.get("scopes", [])),
        )
    return await call_next(request)


def _gateway_error(request: Request, status_code: int, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "serverTime": now_ms(),
            "data": None,
            "requestId": getattr(request.state, "request_id", ""),
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def _proxy_get(request: Request, upstream_url: str, path: str) -> JSONResponse:
    identity = get_api_identity(request)
    settings = get_settings()
    limit = (
        settings.api_key_rate_limit_per_minute
        if identity.authenticated
        else settings.anonymous_rate_limit_per_minute
    )
    rate_limiter.check(f"{identity.principal}:GET:{path}", limit)

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.get(
                f"{upstream_url}{path}",
                params=dict(request.query_params),
                headers=_forward_headers(request),
            )
        except httpx.HTTPError:
            return JSONResponse(
                status_code=503,
                content={
                    "code": 5001,
                    "message": "Service unavailable",
                    "serverTime": now_ms(),
                    "data": None,
                    "requestId": request.state.request_id,
                },
            )

    return JSONResponse(status_code=response.status_code, content=response.json())


async def _proxy_with_body(
    request: Request,
    upstream_url: str,
    path: str,
    method: str,
) -> JSONResponse:
    identity = get_api_identity(request)
    settings = get_settings()
    limit = (
        settings.api_key_rate_limit_per_minute
        if identity.authenticated
        else settings.anonymous_rate_limit_per_minute
    )
    rate_limiter.check(f"{identity.principal}:{method}:{path}", limit)

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.request(
                method,
                f"{upstream_url}{path}",
                params=dict(request.query_params),
                content=await request.body(),
                headers=_forward_headers(request, include_content_type=True),
            )
        except httpx.HTTPError:
            return JSONResponse(
                status_code=503,
                content={
                    "code": 5001,
                    "message": "Service unavailable",
                    "serverTime": now_ms(),
                    "data": None,
                    "requestId": request.state.request_id,
                },
            )

    return JSONResponse(status_code=response.status_code, content=response.json())


def _forward_headers(request: Request, include_content_type: bool = False) -> dict[str, str]:
    headers = {"X-Request-ID": request.state.request_id}
    for name in ("Authorization", "X-API-Key"):
        value = request.headers.get(name)
        if value:
            headers[name] = value
    if include_content_type:
        headers["Content-Type"] = request.headers.get("Content-Type", "application/json")
    return headers


@app.get("/v1/market/ticker")
async def market_ticker(request: Request) -> JSONResponse:
    return await _proxy_get(request, MARKET_SERVICE_URL, "/v1/market/ticker")


@app.get("/v1/market/kline")
async def market_kline(request: Request) -> JSONResponse:
    return await _proxy_get(request, MARKET_SERVICE_URL, "/v1/market/kline")


@app.get("/v1/market/trades")
async def market_trades(request: Request) -> JSONResponse:
    return await _proxy_get(request, MARKET_SERVICE_URL, "/v1/market/trades")


@app.get("/v1/market/funding")
async def market_funding(request: Request) -> JSONResponse:
    return await _proxy_get(request, MARKET_SERVICE_URL, "/v1/market/funding")


@app.get("/v1/market/openInterest")
async def market_open_interest(request: Request) -> JSONResponse:
    return await _proxy_get(request, MARKET_SERVICE_URL, "/v1/market/openInterest")


@app.get("/v1/market/liquidation")
async def market_liquidation(request: Request) -> JSONResponse:
    return await _proxy_get(request, MARKET_SERVICE_URL, "/v1/market/liquidation")


@app.get("/v1/feature/list")
async def feature_list(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_SERVICE_URL, "/v1/feature/list")


@app.get("/v1/feature/meta")
async def feature_meta(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_SERVICE_URL, "/v1/feature/meta")


@app.get("/v1/feature/current")
async def feature_current(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_SERVICE_URL, "/v1/feature/current")


@app.get("/v1/feature/batch")
async def feature_batch(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_SERVICE_URL, "/v1/feature/batch")


@app.get("/v1/feature/pressure-support")
async def feature_pressure_support(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_SERVICE_URL, "/v1/feature/pressure-support")


@app.get("/v1/feature/history")
async def feature_history(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_SERVICE_URL, "/v1/feature/history")


@app.post("/v1/feature-store/registry")
async def feature_store_registry(request: Request) -> JSONResponse:
    return await _proxy_with_body(
        request,
        FEATURE_STORE_SERVICE_URL,
        "/v1/feature-store/registry",
        "POST",
    )


@app.get("/v1/feature-store/catalog")
async def feature_store_catalog(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_STORE_SERVICE_URL, "/v1/feature-store/catalog")


@app.get("/v1/feature-store/meta")
async def feature_store_meta(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_STORE_SERVICE_URL, "/v1/feature-store/meta")


@app.post("/v1/feature-store/value")
async def feature_store_value(request: Request) -> JSONResponse:
    return await _proxy_with_body(
        request,
        FEATURE_STORE_SERVICE_URL,
        "/v1/feature-store/value",
        "POST",
    )


@app.get("/v1/feature-store/latest")
async def feature_store_latest(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_STORE_SERVICE_URL, "/v1/feature-store/latest")


@app.get("/v1/feature-store/history")
async def feature_store_history(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_STORE_SERVICE_URL, "/v1/feature-store/history")


@app.get("/v1/feature-store/materialize")
async def feature_store_materialize(request: Request) -> JSONResponse:
    return await _proxy_get(request, FEATURE_STORE_SERVICE_URL, "/v1/feature-store/materialize")


@app.delete("/v1/feature-store/registry")
async def feature_store_disable(request: Request) -> JSONResponse:
    return await _proxy_with_body(
        request,
        FEATURE_STORE_SERVICE_URL,
        "/v1/feature-store/registry",
        "DELETE",
    )


@app.get("/v1/ranking/overall")
async def ranking_overall(request: Request) -> JSONResponse:
    return await _proxy_get(request, RANKING_SERVICE_URL, "/v1/ranking/overall")


@app.get("/v1/ranking/longInflow")
async def ranking_long_inflow(request: Request) -> JSONResponse:
    return await _proxy_get(request, RANKING_SERVICE_URL, "/v1/ranking/longInflow")


@app.get("/v1/ranking/momentum")
async def ranking_momentum(request: Request) -> JSONResponse:
    return await _proxy_get(request, RANKING_SERVICE_URL, "/v1/ranking/momentum")


@app.get("/v1/ranking/volume")
async def ranking_volume(request: Request) -> JSONResponse:
    return await _proxy_get(request, RANKING_SERVICE_URL, "/v1/ranking/volume")


@app.post("/v1/ranking/monitor/{ranking_type}")
async def ranking_monitor(request: Request, ranking_type: str) -> JSONResponse:
    return await _proxy_with_body(
        request,
        RANKING_SERVICE_URL,
        f"/v1/ranking/monitor/{ranking_type}",
        "POST",
    )


@app.get("/v1/signal/current")
async def signal_current(request: Request) -> JSONResponse:
    return await _proxy_get(request, SIGNAL_SERVICE_URL, "/v1/signal/current")


@app.get("/v1/signal/longInflow")
async def signal_long_inflow(request: Request) -> JSONResponse:
    return await _proxy_get(request, SIGNAL_SERVICE_URL, "/v1/signal/longInflow")


@app.get("/v1/signal/detail")
async def signal_detail(request: Request) -> JSONResponse:
    return await _proxy_get(request, SIGNAL_SERVICE_URL, "/v1/signal/detail")


@app.get("/v1/signal/history")
async def signal_history(request: Request) -> JSONResponse:
    return await _proxy_get(request, SIGNAL_SERVICE_URL, "/v1/signal/history")


@app.post("/v1/alert/create")
async def alert_create(request: Request) -> JSONResponse:
    require_request_permission(request, "alert.write")
    return await _proxy_with_body(request, ALERT_SERVICE_URL, "/v1/alert/create", "POST")


@app.get("/v1/alert/list")
async def alert_list(request: Request) -> JSONResponse:
    return await _proxy_get(request, ALERT_SERVICE_URL, "/v1/alert/list")


@app.post("/v1/alert/update")
async def alert_update(request: Request) -> JSONResponse:
    require_request_permission(request, "alert.write")
    return await _proxy_with_body(request, ALERT_SERVICE_URL, "/v1/alert/update", "POST")


@app.delete("/v1/alert/{alert_id}")
async def alert_delete(request: Request, alert_id: str) -> JSONResponse:
    require_request_permission(request, "alert.write")
    return await _proxy_with_body(request, ALERT_SERVICE_URL, f"/v1/alert/{alert_id}", "DELETE")


@app.post("/v1/alert/longInflow")
async def alert_long_inflow(request: Request) -> JSONResponse:
    require_request_permission(request, "alert.write")
    return await _proxy_with_body(request, ALERT_SERVICE_URL, "/v1/alert/longInflow", "POST")


@app.post("/v1/alert/signal")
async def alert_signal(request: Request) -> JSONResponse:
    require_request_permission(request, "alert.write")
    return await _proxy_with_body(request, ALERT_SERVICE_URL, "/v1/alert/signal", "POST")


@app.get("/v1/alert/history")
async def alert_history(request: Request) -> JSONResponse:
    return await _proxy_get(request, ALERT_SERVICE_URL, "/v1/alert/history")


@app.post("/v1/rule/create")
async def rule_create(request: Request) -> JSONResponse:
    require_request_permission(request, "rule.write")
    return await _proxy_with_body(request, RULE_SERVICE_URL, "/v1/rule/create", "POST")


@app.get("/v1/rule/list")
async def rule_list(request: Request) -> JSONResponse:
    return await _proxy_get(request, RULE_SERVICE_URL, "/v1/rule/list")


@app.post("/v1/rule/update")
async def rule_update(request: Request) -> JSONResponse:
    require_request_permission(request, "rule.write")
    return await _proxy_with_body(request, RULE_SERVICE_URL, "/v1/rule/update", "POST")


@app.delete("/v1/rule/{rule_id}")
async def rule_delete(request: Request, rule_id: str) -> JSONResponse:
    require_request_permission(request, "rule.write")
    return await _proxy_with_body(request, RULE_SERVICE_URL, f"/v1/rule/{rule_id}", "DELETE")


@app.post("/v1/rule/evaluate")
async def rule_evaluate(request: Request) -> JSONResponse:
    require_request_permission(request, "rule.write")
    return await _proxy_with_body(request, RULE_SERVICE_URL, "/v1/rule/evaluate", "POST")


@app.get("/v1/screener/list")
async def screener_list(request: Request) -> JSONResponse:
    return await _proxy_get(request, SCREENER_SERVICE_URL, "/v1/screener/list")


@app.post("/v1/screener/query")
async def screener_query(request: Request) -> JSONResponse:
    return await _proxy_with_body(request, SCREENER_SERVICE_URL, "/v1/screener/query", "POST")


@app.post("/v1/screener/longInflow")
async def screener_long_inflow(request: Request) -> JSONResponse:
    return await _proxy_with_body(request, SCREENER_SERVICE_URL, "/v1/screener/longInflow", "POST")


@app.post("/v1/screener/custom")
async def screener_custom(request: Request) -> JSONResponse:
    return await _proxy_with_body(request, SCREENER_SERVICE_URL, "/v1/screener/custom", "POST")


@app.get("/v1/history/snapshot")
async def history_snapshot(request: Request) -> JSONResponse:
    return await _proxy_get(request, HISTORY_SERVICE_URL, "/v1/history/snapshot")


@app.get("/v1/history/timeline")
async def history_timeline(request: Request) -> JSONResponse:
    return await _proxy_get(request, HISTORY_SERVICE_URL, "/v1/history/timeline")


@app.get("/v1/history/ranking-monitor/events")
async def history_ranking_monitor_events(request: Request) -> JSONResponse:
    return await _proxy_get(request, HISTORY_SERVICE_URL, "/v1/history/ranking-monitor/events")


@app.post("/v1/score/calculate")
async def score_calculate(request: Request) -> JSONResponse:
    require_request_permission(request, "score.read")
    return await _proxy_with_body(request, SCORE_SERVICE_URL, "/v1/score/calculate", "POST")


@app.post("/v1/score/batch")
async def score_batch(request: Request) -> JSONResponse:
    require_request_permission(request, "score.read")
    return await _proxy_with_body(request, SCORE_SERVICE_URL, "/v1/score/batch", "POST")


@app.get("/v1/ai/model")
async def ai_model(request: Request) -> JSONResponse:
    return await _proxy_get(request, AI_SERVICE_URL, "/v1/ai/model")


@app.post("/v1/ai/predict")
async def ai_predict(request: Request) -> JSONResponse:
    return await _proxy_with_body(request, AI_SERVICE_URL, "/v1/ai/predict", "POST")


@app.post("/v1/ai/explain")
async def ai_explain(request: Request) -> JSONResponse:
    return await _proxy_with_body(request, AI_SERVICE_URL, "/v1/ai/explain", "POST")


@app.get("/v1/notification/channels")
async def notification_channels(request: Request) -> JSONResponse:
    return await _proxy_get(
        request,
        NOTIFICATION_SERVICE_URL,
        "/v1/notification/channels",
    )


@app.post("/v1/notification/send")
async def notification_send(request: Request) -> JSONResponse:
    require_request_permission(request, "notification.write")
    return await _proxy_with_body(
        request,
        NOTIFICATION_SERVICE_URL,
        "/v1/notification/send",
        "POST",
    )


@app.get("/v1/notification/history")
async def notification_history(request: Request) -> JSONResponse:
    return await _proxy_get(
        request,
        NOTIFICATION_SERVICE_URL,
        "/v1/notification/history",
    )


@app.get("/v1/notification/preferences")
async def notification_preferences(request: Request) -> JSONResponse:
    return await _proxy_get(
        request,
        NOTIFICATION_SERVICE_URL,
        "/v1/notification/preferences",
    )


@app.post("/v1/notification/preferences")
async def notification_preferences_update(request: Request) -> JSONResponse:
    require_request_permission(request, "notification.write")
    return await _proxy_with_body(
        request,
        NOTIFICATION_SERVICE_URL,
        "/v1/notification/preferences",
        "POST",
    )


@app.post("/v1/user/register")
async def user_register(request: Request) -> JSONResponse:
    return await _proxy_with_body(request, USER_SERVICE_URL, "/v1/user/register", "POST")


@app.post("/v1/user/login")
async def user_login(request: Request) -> JSONResponse:
    return await _proxy_with_body(request, USER_SERVICE_URL, "/v1/user/login", "POST")


@app.post("/v1/user/logout")
async def user_logout(request: Request) -> JSONResponse:
    require_request_permission(request, "user.read")
    return await _proxy_with_body(request, USER_SERVICE_URL, "/v1/user/logout", "POST")


@app.post("/v1/user/password")
async def user_change_password(request: Request) -> JSONResponse:
    require_request_permission(request, "user.write")
    return await _proxy_with_body(request, USER_SERVICE_URL, "/v1/user/password", "POST")


@app.get("/v1/user/profile")
async def user_profile(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/user/profile")


@app.post("/v1/user/api-keys")
async def user_api_key_create(request: Request) -> JSONResponse:
    require_request_permission(request, "api_key.write")
    return await _proxy_with_body(request, USER_SERVICE_URL, "/v1/user/api-keys", "POST")


@app.get("/v1/user/api-keys")
async def user_api_key_list(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/user/api-keys")


@app.delete("/v1/user/api-keys/{key_id}")
async def user_api_key_disable(request: Request, key_id: str) -> JSONResponse:
    require_request_permission(request, "api_key.write")
    return await _proxy_with_body(
        request,
        USER_SERVICE_URL,
        f"/v1/user/api-keys/{key_id}",
        "DELETE",
    )


@app.get("/v1/user/plans")
async def user_plans(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/user/plans")


@app.get("/v1/user/subscription")
async def user_subscription(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/user/subscription")


@app.get("/v1/user/usage")
async def user_usage(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/user/usage")


@app.post("/v1/user/usage/record")
async def user_usage_record(request: Request) -> JSONResponse:
    require_request_permission(request, "user.write")
    return await _proxy_with_body(request, USER_SERVICE_URL, "/v1/user/usage/record", "POST")


@app.post("/v1/user/events")
async def user_events(request: Request) -> JSONResponse:
    require_request_permission(request, "user.write")
    return await _proxy_with_body(request, USER_SERVICE_URL, "/v1/user/events", "POST")


@app.get("/v1/admin/snapshot")
async def admin_snapshot(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/admin/snapshot")


@app.get("/v1/admin/users")
async def admin_users(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/admin/users")


@app.get("/v1/admin/api-keys")
async def admin_api_keys(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/admin/api-keys")


@app.get("/v1/admin/audit")
async def admin_audit(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/admin/audit")


@app.get("/v1/admin/roles")
async def admin_roles(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/admin/roles")


@app.get("/v1/admin/operations")
async def admin_operations(request: Request) -> JSONResponse:
    return await _proxy_get(request, USER_SERVICE_URL, "/v1/admin/operations")


@app.post("/v1/admin/users/{user_id}")
async def admin_update_user(request: Request, user_id: str) -> JSONResponse:
    return await _proxy_with_body(request, USER_SERVICE_URL, f"/v1/admin/users/{user_id}", "POST")
