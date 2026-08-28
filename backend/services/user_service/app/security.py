import base64
import hashlib
import hmac
import json
import secrets

from mip_common.config import get_settings
from mip_common.responses import ServiceError, now_ms


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _algorithm, salt, digest = stored.split("$", 2)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), f"pbkdf2_sha256${salt}${digest}")


def create_access_token(user_id: str, role: str, plan: str) -> str:
    settings = get_settings()
    issued_at = now_ms() // 1000
    payload = {
        "userId": user_id,
        "role": role,
        "plan": plan,
        "iat": issued_at,
        "exp": issued_at + settings.access_token_ttl_seconds,
        "jti": secrets.token_urlsafe(16),
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _sign(body)
    return f"{body}.{signature}"


def verify_access_token(token: str) -> dict:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ServiceError(1001, "Invalid token") from exc
    if not hmac.compare_digest(_sign(body), signature):
        raise ServiceError(1001, "Invalid token")
    payload = json.loads(base64.urlsafe_b64decode(_pad(body)))
    if int(payload.get("exp", 0)) < now_ms() // 1000:
        raise ServiceError(1003, "Token expired")
    return payload


def generate_api_key() -> tuple[str, str, str]:
    api_key = f"ms_live_{secrets.token_urlsafe(24)}"
    secret = secrets.token_urlsafe(32)
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    return api_key, secret, secret_hash


def _sign(body: str) -> str:
    digest = hmac.new(get_settings().jwt_secret.encode(), body.encode(), hashlib.sha256).digest()
    return _b64(digest)


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _pad(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode()
