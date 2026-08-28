import asyncio

from mip_common.models import model_to_dict
from services.user_service.app.repositories import InMemoryUserRepository
from services.user_service.app.schemas import (
    ApiKeyCreateRequest,
    UsageRecordRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from services.user_service.app.services import UserService


async def main() -> None:
    service = UserService(InMemoryUserRepository())
    profile = await service.register(
        UserRegisterRequest(email="demo@example.com", password="password123", plan="pro")
    )
    token = await service.login(UserLoginRequest(email="demo@example.com", password="password123"))
    created_key = await service.create_api_key(
        profile.userId,
        ApiKeyCreateRequest(name="research", scopes=["market.read", "ranking.read"]),
    )
    keys = await service.list_api_keys(profile.userId)
    disabled = await service.disable_api_key(profile.userId, created_key.keyId)
    plans = service.plans()
    subscription = await service.subscription(profile.userId)
    usage = await service.record_usage(
        profile.userId,
        UsageRecordRequest(metric="api_requests", amount=25),
    )
    print(model_to_dict(profile))
    print(model_to_dict(token))
    print(model_to_dict(created_key))
    print([model_to_dict(key) for key in keys])
    print(model_to_dict(disabled))
    print([model_to_dict(plan) for plan in plans])
    print(model_to_dict(subscription))
    print(model_to_dict(usage))


if __name__ == "__main__":
    asyncio.run(main())
