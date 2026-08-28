import base64
import hashlib
import hmac
import json
from dataclasses import dataclass

from fastapi import Request

from .config import get_settings
from .responses import ServiceError, now_ms


@dataclass(frozen=True)
class ApiIdentity:
    principal: str
    plan: str
    authenticated: bool
    role: str = "anonymous"
    scopes: frozenset[str] = frozenset()


def get_api_identity(request: Request) -> ApiIdentity:
    cached_identity = getattr(getattr(request, "state", None), "api_identity", None)
    if isinstance(cached_identity, ApiIdentity):
        return cached_identity
    api_key = request.headers.get("X-API-KEY") or request.headers.get("X-API-Key")
    settings = get_settings()
    configured_keys = settings.api_key_set

    authorization = request.headers.get("Authorization")
    if authorization:
        payload = verify_bearer_token(authorization)
        return ApiIdentity(
            principal=f"user:{payload['userId']}",
            plan=str(payload.get("plan", "free")),
            authenticated=True,
            role=str(payload.get("role", "user")),
        )

    if api_key:
        # API keys are an explicit deployment allow-list until a shared key
        # repository is introduced.  Never treat an arbitrary header as a key.
        if api_key not in configured_keys:
            raise ServiceError(1001, "Invalid API Key")
        return ApiIdentity(
            principal=f"api-key:{api_key}",
            plan="pro",
            authenticated=True,
            role="readonly",
            scopes=frozenset({"market.read"}),
        )

    client = getattr(request, "client", None)
    client_host = client.host if client else "unknown"
    return ApiIdentity(principal=f"anonymous:{client_host}", plan="free", authenticated=False)


def verify_bearer_token(authorization: str) -> dict[str, object]:
    """Verify the locally signed access token before it is used for RBAC."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ServiceError(1001, "Invalid token")
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ServiceError(1001, "Invalid token") from exc

    expected = _sign_token_body(body)
    if not hmac.compare_digest(expected, signature):
        raise ServiceError(1001, "Invalid token")
    try:
        payload = json.loads(base64.urlsafe_b64decode(_pad_base64(body)))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ServiceError(1001, "Invalid token") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("userId"), str):
        raise ServiceError(1001, "Invalid token")
    if int(payload.get("exp", 0)) < now_ms() // 1000:
        raise ServiceError(1003, "Token expired")
    return payload


def _sign_token_body(body: str) -> str:
    digest = hmac.new(get_settings().jwt_secret.encode(), body.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def _pad_base64(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode()
