import hmac
from typing import Protocol

from .schemas import ApiKeyInfo, Subscription, UsageSummary, UserBehaviorEvent, UserProfile


class StoredUser(UserProfile):
    passwordHash: str


class StoredApiKey(ApiKeyInfo):
    secretHash: str


class UserRepository(Protocol):
    async def save_user(self, user: StoredUser) -> None:
        ...

    async def get_user(self, user_id: str) -> StoredUser | None:
        ...

    async def get_user_by_email(self, email: str) -> StoredUser | None:
        ...

    async def list_users(self) -> list[StoredUser]:
        ...

    async def save_api_key(self, api_key: StoredApiKey) -> None:
        ...

    async def list_api_keys(self, user_id: str) -> list[StoredApiKey]:
        ...

    async def list_all_api_keys(self) -> list[StoredApiKey]:
        ...

    async def get_api_key(self, key_id: str) -> StoredApiKey | None:
        ...

    async def get_api_key_by_value(self, api_key: str) -> StoredApiKey | None:
        ...

    async def save_subscription(self, subscription: Subscription) -> None:
        ...

    async def get_subscription(self, user_id: str) -> Subscription | None:
        ...

    async def list_subscriptions(self) -> list[Subscription]:
        ...

    async def save_usage(self, summary: UsageSummary) -> None:
        ...

    async def get_usage(self, user_id: str) -> UsageSummary | None:
        ...

    async def list_usage(self) -> list[UsageSummary]:
        ...

    async def revoke_token(self, jti: str, expires_at: int) -> None:
        ...

    async def is_token_revoked(self, jti: str) -> bool:
        ...

    async def save_behavior_event(self, event: UserBehaviorEvent) -> None:
        ...

    async def list_behavior_events(self, limit: int = 1000) -> list[UserBehaviorEvent]:
        ...


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._users: dict[str, StoredUser] = {}
        self._api_keys: dict[str, StoredApiKey] = {}
        self._subscriptions: dict[str, Subscription] = {}
        self._usage: dict[str, UsageSummary] = {}
        self._revoked_tokens: dict[str, int] = {}
        self._behavior_events: list[UserBehaviorEvent] = []

    async def save_user(self, user: StoredUser) -> None:
        self._users[user.userId] = user

    async def get_user(self, user_id: str) -> StoredUser | None:
        return self._users.get(user_id)

    async def get_user_by_email(self, email: str) -> StoredUser | None:
        normalized = email.lower()
        for user in self._users.values():
            if user.email.lower() == normalized:
                return user
        return None

    async def list_users(self) -> list[StoredUser]:
        return sorted(self._users.values(), key=lambda row: row.createdAt, reverse=True)

    async def save_api_key(self, api_key: StoredApiKey) -> None:
        self._api_keys[api_key.keyId] = api_key

    async def list_api_keys(self, user_id: str) -> list[StoredApiKey]:
        rows = [row for row in self._api_keys.values() if row.userId == user_id]
        rows.sort(key=lambda row: row.createdAt, reverse=True)
        return rows

    async def list_all_api_keys(self) -> list[StoredApiKey]:
        return sorted(self._api_keys.values(), key=lambda row: row.createdAt, reverse=True)

    async def get_api_key(self, key_id: str) -> StoredApiKey | None:
        return self._api_keys.get(key_id)

    async def get_api_key_by_value(self, api_key: str) -> StoredApiKey | None:
        return next(
            (
                row
                for row in self._api_keys.values()
                if hmac.compare_digest(row.apiKey, api_key)
            ),
            None,
        )

    async def save_subscription(self, subscription: Subscription) -> None:
        self._subscriptions[subscription.userId] = subscription

    async def get_subscription(self, user_id: str) -> Subscription | None:
        return self._subscriptions.get(user_id)

    async def list_subscriptions(self) -> list[Subscription]:
        return sorted(self._subscriptions.values(), key=lambda row: row.startedAt, reverse=True)

    async def save_usage(self, summary: UsageSummary) -> None:
        self._usage[summary.userId] = summary

    async def get_usage(self, user_id: str) -> UsageSummary | None:
        return self._usage.get(user_id)

    async def list_usage(self) -> list[UsageSummary]:
        return sorted(self._usage.values(), key=lambda row: row.periodStart, reverse=True)

    async def revoke_token(self, jti: str, expires_at: int) -> None:
        self._revoked_tokens[jti] = expires_at

    async def is_token_revoked(self, jti: str) -> bool:
        return jti in self._revoked_tokens

    async def save_behavior_event(self, event: UserBehaviorEvent) -> None:
        self._behavior_events.append(event)

    async def list_behavior_events(self, limit: int = 1000) -> list[UserBehaviorEvent]:
        return list(reversed(self._behavior_events[-max(1, min(limit, 5000)) :]))
