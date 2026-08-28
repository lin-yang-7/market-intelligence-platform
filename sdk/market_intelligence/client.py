import json as jsonlib
import time
from collections.abc import Mapping
from typing import Any

import httpx
from mip_common.signature import sign_request

from .errors import ApiError, AuthenticationError, ParameterError, RateLimitError, ServerError
from .resources import (
    AlertResource,
    FeatureResource,
    FeatureStoreResource,
    HistoryResource,
    MarketResource,
    RankingResource,
    RuleResource,
    ScoreResource,
    ScreenerResource,
    SignalResource,
    UserResource,
)


class Client:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str | None = None,
        secret: str | None = None,
        access_token: str | None = None,
        timeout: float = 10.0,
        retries: int = 2,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.secret = secret
        self.access_token = access_token
        self.retries = retries
        self._client = httpx.Client(timeout=timeout, transport=transport)

        self.market = MarketResource(self)
        self.feature = FeatureResource(self)
        self.feature_store = FeatureStoreResource(self)
        self.ranking = RankingResource(self)
        self.screener = ScreenerResource(self)
        self.signal = SignalResource(self)
        self.alert = AlertResource(self)
        self.history = HistoryResource(self)
        self.score = ScoreResource(self)
        self.rule = RuleResource(self)
        self.user = UserResource(self)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def set_access_token(self, access_token: str) -> None:
        self.access_token = access_token

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: Mapping[str, Any] | None = None) -> Any:
        return self._request("POST", path, json=json)

    def delete(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        return self._request("DELETE", path, params=params)

    def _request(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        last_error: httpx.HTTPError | None = None
        for attempt in range(self.retries + 1):
            try:
                filtered_params = {
                    key: value
                    for key, value in (params or {}).items()
                    if value is not None
                }
                body = json if json is not None else None
                body_bytes = (
                    jsonlib.dumps(body, separators=(",", ":")).encode()
                    if body is not None
                    else b""
                )
                response = self._client.request(
                    method,
                    f"{self.base_url}{path}",
                    params=filtered_params,
                    content=body_bytes if body is not None else None,
                    headers=self._headers(method, path, body_bytes),
                )
                return self._parse_response(response)
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise ServerError("Network request failed") from exc
                time.sleep(0.1 * (2**attempt))
        raise ServerError("Network request failed") from last_error

    def _headers(self, method: str, path: str, body: bytes = b"") -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if body:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.secret:
            timestamp = str(int(time.time()))
            headers["X-Timestamp"] = timestamp
            headers["X-Signature"] = sign_request(self.secret, timestamp, method, path, body)
        return headers

    def _parse_response(self, response: httpx.Response) -> Any:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ServerError(
                "Invalid JSON response",
                status_code=response.status_code,
            ) from exc

        code = payload.get("code")
        if response.is_success and code == 0:
            return payload.get("data")

        message = payload.get("message", "API request failed")
        request_id = payload.get("requestId")
        if response.status_code in {401, 403} or code in {1001, 9002, 9003}:
            raise AuthenticationError(message, code, response.status_code, request_id)
        if response.status_code == 429 or code == 1002:
            raise RateLimitError(message, code, response.status_code, request_id)
        if response.status_code < 500 and code:
            raise ParameterError(message, code, response.status_code, request_id)
        raise ApiError(message, code, response.status_code, request_id)
