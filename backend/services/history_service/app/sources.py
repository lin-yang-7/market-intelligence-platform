from typing import Any, Protocol

import httpx
from mip_common.responses import ServiceError


class HistorySource(Protocol):
    async def get(self, base_url: str, path: str, params: dict[str, Any]) -> Any: ...


class HttpHistorySource:
    async def get(self, base_url: str, path: str, params: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                response = await client.get(f"{base_url}{path}", params=params)
            except httpx.HTTPError as exc:
                raise ServiceError(5001, "History upstream unavailable") from exc
        payload = response.json()
        if response.status_code >= 400 or payload.get("code") != 0:
            raise ServiceError(
                payload.get("code", 5002),
                payload.get("message", "History upstream failed"),
            )
        return payload["data"]
