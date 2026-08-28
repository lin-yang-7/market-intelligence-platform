import time

import pytest
from mip_common.responses import ServiceError
from mip_common.signature import sign_request, verify_request_signature


def test_verify_request_signature_accepts_valid_signature() -> None:
    timestamp = str(int(time.time()))
    signature = sign_request("secret", timestamp, "POST", "/v1/rule/create", b'{"a":1}')

    verify_request_signature(
        "secret",
        timestamp,
        signature,
        "POST",
        "/v1/rule/create",
        b'{"a":1}',
    )


def test_verify_request_signature_rejects_invalid_signature() -> None:
    timestamp = str(int(time.time()))

    with pytest.raises(ServiceError) as exc:
        verify_request_signature("secret", timestamp, "bad", "GET", "/v1/market/ticker")

    assert exc.value.code == 1005


def test_verify_request_signature_rejects_expired_timestamp() -> None:
    timestamp = str(int(time.time()) - 1000)
    signature = sign_request("secret", timestamp, "GET", "/v1/market/ticker")

    with pytest.raises(ServiceError) as exc:
        verify_request_signature("secret", timestamp, signature, "GET", "/v1/market/ticker")

    assert exc.value.message == "Request timestamp expired"
