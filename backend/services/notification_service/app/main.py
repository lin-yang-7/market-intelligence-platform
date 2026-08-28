from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import StreamingResponse
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .broker import sse_broker
from .dependencies import get_notification_service
from .schemas import NotificationPreference, NotificationSendRequest
from .services import NotificationService

app = FastAPI(title="Notification Service", version="0.1.0")
install_logging(app, "notification-service")
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "notification-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/notification/channels")
async def channels(
    request: Request,
    service: NotificationService = Depends(get_notification_service),
):
    return ok(service.channels(), request_id=request.state.request_id)


@app.post("/v1/notification/send")
async def send_notification(
    request: Request,
    payload: NotificationSendRequest,
    service: NotificationService = Depends(get_notification_service),
):
    return ok(await service.send(payload), request_id=request.state.request_id)


@app.get("/v1/notification/stream")
async def notification_stream():
    return StreamingResponse(
        sse_broker.subscribe(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/v1/notification/history")
async def notification_history(
    request: Request,
    userId: str | None = Query(default=None, min_length=1, max_length=64),
    limit: int = Query(default=100, ge=1, le=1000),
    service: NotificationService = Depends(get_notification_service),
):
    return ok(await service.history(userId, limit), request_id=request.state.request_id)


@app.get("/v1/notification/preferences")
async def notification_preferences(
    request: Request,
    userId: str = Query(default="default", min_length=1, max_length=64),
    service: NotificationService = Depends(get_notification_service),
):
    return ok(await service.preference(userId), request_id=request.state.request_id)


@app.post("/v1/notification/preferences")
async def update_notification_preferences(
    request: Request,
    payload: NotificationPreference,
    service: NotificationService = Depends(get_notification_service),
):
    return ok(await service.save_preference(payload), request_id=request.state.request_id)
