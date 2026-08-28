from fastapi import Request
from fastapi.responses import JSONResponse

from .responses import ServiceError, now_ms


def error_response(
    request: Request,
    code: int,
    message: str,
    status_code: int = 400,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "serverTime": now_ms(),
            "data": None,
            "requestId": getattr(request.state, "request_id", request.headers.get("X-Request-ID")),
        },
    )


async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    status_code = 404 if exc.code == 3001 else 400
    if exc.code in {5000, 5001}:
        status_code = 503
    return error_response(request, exc.code, exc.message, status_code=status_code)

