import pytest
from mip_common.rate_limit import FixedWindowRateLimiter
from mip_common.responses import ServiceError


def test_fixed_window_rate_limiter_rejects_after_limit() -> None:
    limiter = FixedWindowRateLimiter()
    limiter.check("anonymous:test", limit=1)

    with pytest.raises(ServiceError) as exc_info:
        limiter.check("anonymous:test", limit=1)

    assert exc_info.value.code == 1003
