import json

import httpx
import pytest
from market_intelligence import Client, ParameterError
from mip_common.signature import verify_request_signature


def response(data, status_code: int = 200):
    return httpx.Response(
        status_code,
        json={
            "code": 0,
            "message": "success",
            "serverTime": 1700000000000,
            "data": data,
            "requestId": "sdk-test",
        },
    )


def test_sdk_injects_auth_headers_and_returns_data() -> None:
    seen_headers = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers["api_key"] = request.headers.get("X-API-Key")
        seen_headers["authorization"] = request.headers.get("Authorization")
        assert request.url.path == "/v1/ranking/longInflow"
        assert request.url.params["limit"] == "5"
        return response([{"symbol": "BTCUSDT"}])

    client = Client(
        base_url="http://testserver",
        api_key="key-1",
        access_token="token-1",
        transport=httpx.MockTransport(handler),
    )

    data = client.ranking.long_inflow(limit=5)

    assert data == [{"symbol": "BTCUSDT"}]
    assert seen_headers == {"api_key": "key-1", "authorization": "Bearer token-1"}


def test_sdk_login_stores_access_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/user/login":
            assert json.loads(request.content) == {
                "email": "demo@example.com",
                "password": "password123",
            }
            return response({"accessToken": "token-2", "profile": {"email": "demo@example.com"}})
        assert request.headers["Authorization"] == "Bearer token-2"
        return response({"email": "demo@example.com"})

    client = Client(base_url="http://testserver", transport=httpx.MockTransport(handler))

    login = client.user.login("demo@example.com", "password123")
    profile = client.user.profile()

    assert login["accessToken"] == "token-2"
    assert profile["email"] == "demo@example.com"


def test_sdk_signs_requests_when_secret_is_configured() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        verify_request_signature(
            "secret-1",
            request.headers.get("X-Timestamp"),
            request.headers.get("X-Signature"),
            request.method,
            request.url.path,
            request.content,
        )
        return response({"ok": True})

    client = Client(
        base_url="http://testserver",
        api_key="key-1",
        secret="secret-1",
        transport=httpx.MockTransport(handler),
    )

    data = client.rule.create({"name": "test", "scope": "signal", "conditions": {}})

    assert data == {"ok": True}


def test_sdk_converts_api_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "code": 4002,
                "message": "Invalid ranking type",
                "data": None,
                "requestId": "bad-request",
            },
        )

    client = Client(base_url="http://testserver", transport=httpx.MockTransport(handler))

    with pytest.raises(ParameterError) as exc:
        client.ranking.overall()

    assert exc.value.code == 4002
    assert exc.value.request_id == "bad-request"
