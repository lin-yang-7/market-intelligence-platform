import time
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


def now_ms() -> int:
    return int(time.time() * 1000)


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    serverTime: int = Field(default_factory=now_ms)
    data: T
    requestId: str | None = None


class ServiceError(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def ok(data: T, request_id: str | None = None) -> ApiResponse[T]:
    return ApiResponse(data=data, requestId=request_id)
