import json
from typing import Any

from pydantic import BaseModel

from .models import model_to_json, validate_model


async def redis_get_model(redis_client, key: str, model_class):
    payload = await redis_client.get(key)
    if not payload:
        return None
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    return validate_model(model_class, json.loads(payload))


async def redis_set_model(
    redis_client,
    key: str,
    model: BaseModel,
    ttl_seconds: int | None = None,
) -> None:
    if ttl_seconds:
        await redis_client.set(key, model_to_json(model), ex=ttl_seconds)
    else:
        await redis_client.set(key, model_to_json(model))


async def redis_get_json_list(redis_client, key: str) -> list[dict[str, Any]]:
    payload = await redis_client.get(key)
    if not payload:
        return []
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    decoded = json.loads(payload)
    if not isinstance(decoded, list):
        return []
    return [item for item in decoded if isinstance(item, dict)]


async def redis_set_json_list(
    redis_client,
    key: str,
    values: list[BaseModel],
    ttl_seconds: int | None = None,
) -> None:
    payload = "[" + ",".join(model_to_json(value) for value in values) + "]"
    if ttl_seconds:
        await redis_client.set(key, payload, ex=ttl_seconds)
    else:
        await redis_client.set(key, payload)
