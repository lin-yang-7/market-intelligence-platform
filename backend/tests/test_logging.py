import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient
from mip_common.logging import JsonLogFormatter, install_logging
from mip_common.middleware import RequestIdMiddleware


def test_json_log_formatter_includes_extra_fields() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="mip.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.service = "unit-test"
    record.request_id = "req-1"

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "mip.test"
    assert payload["message"] == "hello"
    assert payload["service"] == "unit-test"
    assert payload["request_id"] == "req-1"


def test_request_logging_middleware_emits_structured_log(capfd) -> None:
    app = FastAPI()
    install_logging(app, "test-service")
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(app).get("/ping", headers={"X-Request-ID": "req-123"})
    output = capfd.readouterr().out.strip().splitlines()
    payload = next(item for item in map(json.loads, output) if item["message"] == "http_request")

    assert response.status_code == 200
    assert payload["service"] == "test-service"
    assert payload["request_id"] == "req-123"
    assert payload["path"] == "/ping"
    assert payload["status_code"] == 200
