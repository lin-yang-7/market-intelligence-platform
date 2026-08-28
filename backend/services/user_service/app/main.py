import hmac

from fastapi import Depends, FastAPI, Header, Query, Request
from mip_common.config import get_settings
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .dependencies import get_user_service
from .schemas import (
    AdminUserUpdateRequest,
    ApiKeyCreateRequest,
    PasswordChangeRequest,
    UsageRecordRequest,
    UserBehaviorEventRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from .security import verify_access_token
from .services import UserService

app = FastAPI(title="User Service", version="0.1.0")
install_logging(app, "user-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "user-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/user/register")
async def register(
    request: Request,
    payload: UserRegisterRequest,
    service: UserService = Depends(get_user_service),
):
    return ok(await service.register(payload), request_id=request.state.request_id)


@app.post("/v1/user/login")
async def login(
    request: Request,
    payload: UserLoginRequest,
    service: UserService = Depends(get_user_service),
):
    return ok(await service.login(payload), request_id=request.state.request_id)


@app.get("/v1/user/profile")
async def profile(
    request: Request,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    payload = await _active_auth_payload(authorization, service)
    return ok(await service.profile(payload["userId"]), request_id=request.state.request_id)


@app.post("/v1/user/logout")
async def logout(
    request: Request,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    payload = await _active_auth_payload(authorization, service)
    return ok(await service.revoke_token(payload), request_id=request.state.request_id)


@app.post("/v1/user/password")
async def change_password(
    request: Request,
    payload: PasswordChangeRequest,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(
        await service.change_password(token["userId"], token, payload),
        request_id=request.state.request_id,
    )


@app.post("/v1/user/api-keys")
async def create_api_key(
    request: Request,
    payload: ApiKeyCreateRequest,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(
        await service.create_api_key(token["userId"], payload),
        request_id=request.state.request_id,
    )


@app.get("/v1/user/api-keys")
async def list_api_keys(
    request: Request,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(await service.list_api_keys(token["userId"]), request_id=request.state.request_id)


@app.delete("/v1/user/api-keys/{key_id}")
async def disable_api_key(
    request: Request,
    key_id: str,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(
        await service.disable_api_key(token["userId"], key_id),
        request_id=request.state.request_id,
    )


@app.get("/v1/user/plans")
async def plans(
    request: Request,
    service: UserService = Depends(get_user_service),
):
    return ok(service.plans(), request_id=request.state.request_id)


@app.get("/v1/user/subscription")
async def subscription(
    request: Request,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(await service.subscription(token["userId"]), request_id=request.state.request_id)


@app.get("/v1/user/usage")
async def usage(
    request: Request,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(await service.usage(token["userId"]), request_id=request.state.request_id)


@app.post("/v1/user/usage/record")
async def record_usage(
    request: Request,
    payload: UsageRecordRequest,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(
        await service.record_usage(token["userId"], payload),
        request_id=request.state.request_id,
    )


@app.post("/v1/user/events")
async def record_behavior_event(
    request: Request,
    payload: UserBehaviorEventRequest,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(
        await service.record_behavior(token["userId"], payload),
        request_id=request.state.request_id,
    )


@app.get("/v1/admin/snapshot")
async def admin_snapshot(
    request: Request,
    authorization: str = Header(...),
    limit: int = Query(default=100, ge=1, le=500),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(await service.admin_snapshot(token, limit), request_id=request.state.request_id)


@app.get("/v1/admin/users")
async def admin_users(
    request: Request,
    authorization: str = Header(...),
    limit: int = Query(default=100, ge=1, le=500),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(await service.admin_users(token, limit), request_id=request.state.request_id)


@app.get("/v1/admin/api-keys")
async def admin_api_keys(
    request: Request,
    authorization: str = Header(...),
    limit: int = Query(default=100, ge=1, le=500),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(await service.admin_api_keys(token, limit), request_id=request.state.request_id)


@app.get("/v1/admin/audit")
async def admin_audit(
    request: Request,
    authorization: str = Header(...),
    limit: int = Query(default=100, ge=1, le=500),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(await service.admin_audit_events(token, limit), request_id=request.state.request_id)


@app.get("/v1/admin/roles")
async def admin_roles(
    request: Request,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(await service.admin_roles(token), request_id=request.state.request_id)


@app.get("/v1/admin/operations")
async def admin_operations(
    request: Request,
    authorization: str = Header(...),
    limit: int = Query(default=100, ge=1, le=1000),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(await service.admin_operations(token, limit), request_id=request.state.request_id)


@app.post("/v1/admin/users/{user_id}")
async def admin_update_user(
    request: Request,
    user_id: str,
    payload: AdminUserUpdateRequest,
    authorization: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    token = await _active_auth_payload(authorization, service)
    return ok(
        await service.admin_update_user(token, user_id, payload),
        request_id=request.state.request_id,
    )


@app.get("/internal/api-keys/verify")
async def verify_api_key(
    request: Request,
    x_api_key: str = Header(...),
    x_internal_service_token: str = Header(...),
    service: UserService = Depends(get_user_service),
):
    if not hmac.compare_digest(x_internal_service_token, get_settings().internal_service_token):
        raise ServiceError(1001, "Invalid internal service token")
    return ok(await service.verify_api_key(x_api_key), request_id=request.state.request_id)


def _auth_payload(authorization: str) -> dict:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ServiceError(1001, "Invalid token")
    return verify_access_token(token)


async def _active_auth_payload(authorization: str, service: UserService) -> dict:
    payload = _auth_payload(authorization)
    await service.ensure_token_active(payload)
    return payload
