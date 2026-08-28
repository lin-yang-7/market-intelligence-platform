from types import SimpleNamespace

import pytest
from mip_common.config import get_settings
from mip_common.rbac import require_request_permission
from mip_common.responses import ServiceError
from services.api_gateway.app.main import _forward_headers
from services.user_service.app.security import create_access_token


def test_gateway_forwards_auth_headers() -> None:
    request = SimpleNamespace(
        state=SimpleNamespace(request_id="gateway-auth"),
        headers={
            "Authorization": "Bearer token-123",
            "X-API-Key": "api-key-123",
            "Content-Type": "application/json",
        },
    )

    headers = _forward_headers(request, include_content_type=True)

    assert headers == {
        "X-Request-ID": "gateway-auth",
        "Authorization": "Bearer token-123",
        "X-API-Key": "api-key-123",
        "Content-Type": "application/json",
    }


def test_gateway_permission_allows_valid_authenticated_user() -> None:
    token = create_access_token("usr_1", "user", "pro")
    request = SimpleNamespace(headers={"Authorization": f"Bearer {token}"})

    require_request_permission(request, "rule.write")


def test_gateway_permission_denies_missing_authentication() -> None:
    request = SimpleNamespace(headers={})

    with pytest.raises(ServiceError) as exc:
        require_request_permission(request, "rule.write")

    assert exc.value.code == 1001


def test_gateway_permission_rejects_forged_bearer_token() -> None:
    request = SimpleNamespace(headers={"Authorization": "Bearer token-123", "X-User-Role": "admin"})

    with pytest.raises(ServiceError) as exc:
        require_request_permission(request, "user.write")

    assert exc.value.code == 1001


def test_gateway_permission_rejects_unconfigured_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEYS", raising=False)
    get_settings.cache_clear()
    request = SimpleNamespace(headers={"X-API-Key": "forged-key", "X-API-Scopes": "user.write"})

    with pytest.raises(ServiceError) as exc:
        require_request_permission(request, "user.write")

    assert exc.value.code == 1001
    get_settings.cache_clear()
