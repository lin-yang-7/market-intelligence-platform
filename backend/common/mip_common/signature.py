import hashlib
import hmac
import time

from .responses import ServiceError


def sign_request(secret: str, timestamp: str, method: str, path: str, body: bytes = b"") -> str:
    message = timestamp.encode() + method.upper().encode() + path.encode() + body
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def verify_request_signature(
    secret: str,
    timestamp: str | None,
    signature: str | None,
    method: str,
    path: str,
    body: bytes = b"",
    max_skew_seconds: int = 300,
) -> None:
    if not timestamp or not signature:
        raise ServiceError(1005, "Missing request signature")
    try:
        timestamp_value = int(timestamp)
    except ValueError as exc:
        raise ServiceError(1005, "Invalid request timestamp") from exc
    now = int(time.time())
    if abs(now - timestamp_value) > max_skew_seconds:
        raise ServiceError(1005, "Request timestamp expired")
    expected = sign_request(secret, timestamp, method, path, body)
    if not hmac.compare_digest(expected, signature):
        raise ServiceError(1005, "Invalid request signature")
