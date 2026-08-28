import hashlib

from mip_common.audit import audit_log, record_audit
from mip_common.config import get_settings
from mip_common.models import model_copy_with_update
from mip_common.rbac import ROLE_PERMISSIONS
from mip_common.responses import ServiceError, now_ms

from .repositories import StoredApiKey, StoredUser, UserRepository
from .schemas import (
    AdminRoleDefinition,
    AdminSnapshot,
    AdminSummaryMetric,
    AdminUserRow,
    AdminUserUpdateRequest,
    ApiKeyCreated,
    ApiKeyCreateRequest,
    ApiKeyInfo,
    ApiKeyVerification,
    AuthToken,
    OperationsAnalytics,
    PasswordChangeRequest,
    Plan,
    Subscription,
    UsageRecordRequest,
    UsageSummary,
    UserBehaviorEvent,
    UserBehaviorEventRequest,
    UserLoginRequest,
    UserProfile,
    UserRegisterRequest,
)
from .security import create_access_token, generate_api_key, hash_password, verify_password

PLANS: dict[str, Plan] = {
    "free": Plan(
        planId="free",
        name="Free",
        priceMonthly=0,
        requestLimitPerDay=1_000,
        features=["market.basic", "dashboard"],
    ),
    "pro": Plan(
        planId="pro",
        name="Pro",
        priceMonthly=49,
        requestLimitPerDay=100_000,
        features=["market.full", "ranking", "signal", "notification"],
    ),
    "enterprise": Plan(
        planId="enterprise",
        name="Enterprise",
        priceMonthly=499,
        requestLimitPerDay=1_000_000,
        features=["market.full", "ranking", "signal", "notification", "dedicated_support"],
    ),
}


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def register(self, request: UserRegisterRequest) -> UserProfile:
        if request.plan not in PLANS:
            raise ServiceError(9006, "Invalid subscription plan")
        existing = await self.repository.get_user_by_email(request.email)
        if existing:
            raise ServiceError(9001, "User already exists")
        timestamp = now_ms()
        user = StoredUser(
            userId=self._id("usr", request.email, timestamp),
            email=request.email.lower(),
            passwordHash=hash_password(request.password),
            role=self._role_for_email(request.email),
            plan=request.plan,
            status="active",
            createdAt=timestamp,
            updatedAt=timestamp,
        )
        await self.repository.save_user(user)
        await self.repository.save_subscription(
            Subscription(
                subscriptionId=self._id("sub", user.userId, request.plan, timestamp),
                userId=user.userId,
                planId=request.plan,
                status="active",
                startedAt=timestamp,
            )
        )
        await self.repository.save_usage(self._empty_usage(user.userId, request.plan, timestamp))
        await self._record_behavior(user.userId, "signup", {"plan": request.plan})
        return self._profile(user)

    async def login(self, request: UserLoginRequest) -> AuthToken:
        user = await self.repository.get_user_by_email(request.email)
        if user is None or not verify_password(request.password, user.passwordHash):
            raise ServiceError(9002, "Invalid email or password")
        if user.status != "active":
            raise ServiceError(9003, "User disabled")
        settings = get_settings()
        record_audit(user.userId, "login", "user", "success")
        await self._record_behavior(user.userId, "login", {"plan": user.plan})
        return AuthToken(
            accessToken=create_access_token(user.userId, user.role, user.plan),
            expiresIn=settings.access_token_ttl_seconds,
            profile=self._profile(user),
        )

    async def revoke_token(self, token_payload: dict) -> dict[str, str]:
        jti = str(token_payload.get("jti") or "")
        if not jti:
            raise ServiceError(1001, "Invalid token")
        await self.repository.revoke_token(jti, int(token_payload.get("exp", 0)))
        record_audit(str(token_payload.get("userId", "")), "logout", "token", "success")
        return {"status": "revoked"}

    async def ensure_token_active(self, token_payload: dict) -> None:
        jti = str(token_payload.get("jti") or "")
        if jti and await self.repository.is_token_revoked(jti):
            raise ServiceError(1001, "Token revoked")

    async def change_password(
        self,
        user_id: str,
        token_payload: dict,
        request: PasswordChangeRequest,
    ) -> dict[str, str]:
        user = await self.repository.get_user(user_id)
        if user is None:
            raise ServiceError(9004, "User not found")
        if not verify_password(request.oldPassword, user.passwordHash):
            raise ServiceError(9002, "Invalid email or password")
        updated = model_copy_with_update(
            user,
            {"passwordHash": hash_password(request.newPassword), "updatedAt": now_ms()},
        )
        await self.repository.save_user(updated)
        await self.revoke_token(token_payload)
        record_audit(user_id, "change_password", "user", "success")
        return {"status": "password_changed"}

    async def admin_snapshot(self, token_payload: dict, limit: int = 100) -> AdminSnapshot:
        self._require_admin(token_payload)
        users = await self.repository.list_users()
        api_keys = await self.repository.list_all_api_keys()
        subscriptions = await self.repository.list_subscriptions()
        usage = await self.repository.list_usage()
        usage_by_user = {row.userId: row for row in usage}
        subscription_by_user = {row.userId: row for row in subscriptions}
        api_key_counts: dict[str, int] = {}
        for row in api_keys:
            api_key_counts[row.userId] = api_key_counts.get(row.userId, 0) + 1
        rows = [
            AdminUserRow(
                profile=self._profile(user),
                subscription=subscription_by_user.get(user.userId),
                usage=usage_by_user.get(user.userId),
                apiKeyCount=api_key_counts.get(user.userId, 0),
            )
            for user in users[: max(1, min(limit, 500))]
        ]
        total_requests = sum(row.usage.get("api_requests", 0) for row in usage)
        active_users = sum(1 for user in users if user.status == "active")
        pro_users = sum(1 for user in users if user.plan in {"pro", "enterprise"})
        disabled_keys = sum(1 for row in api_keys if row.status != "active")
        record_audit(str(token_payload["userId"]), "admin_snapshot", "admin", "success")
        return AdminSnapshot(
            metrics=[
                AdminSummaryMetric(label="users", value=len(users), tone="neutral"),
                AdminSummaryMetric(label="active_users", value=active_users, tone="positive"),
                AdminSummaryMetric(label="paid_users", value=pro_users, tone="positive"),
                AdminSummaryMetric(label="api_requests", value=total_requests, tone="neutral"),
                AdminSummaryMetric(label="api_keys", value=len(api_keys), tone="neutral"),
                AdminSummaryMetric(label="disabled_keys", value=disabled_keys, tone="warning"),
            ],
            users=rows,
            apiKeys=[self._api_key_info(row) for row in api_keys[: max(1, min(limit, 500))]],
            subscriptions=subscriptions[: max(1, min(limit, 500))],
            usage=usage[: max(1, min(limit, 500))],
            auditEvents=[
                {
                    "actor": event.actor,
                    "action": event.action,
                    "resource": event.resource,
                    "result": event.result,
                    "timestamp": event.timestamp,
                    "metadata": event.metadata,
                }
                for event in audit_log.list_events(limit=limit)
            ],
        )

    async def profile(self, user_id: str) -> UserProfile:
        user = await self.repository.get_user(user_id)
        if user is None:
            raise ServiceError(9004, "User not found")
        return self._profile(user)

    async def admin_users(self, token_payload: dict, limit: int = 100) -> list[AdminUserRow]:
        return (await self.admin_snapshot(token_payload, limit)).users

    async def admin_api_keys(self, token_payload: dict, limit: int = 100) -> list[ApiKeyInfo]:
        return (await self.admin_snapshot(token_payload, limit)).apiKeys

    async def admin_audit_events(
        self,
        token_payload: dict,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        return (await self.admin_snapshot(token_payload, limit)).auditEvents

    async def admin_roles(self, token_payload: dict) -> list[AdminRoleDefinition]:
        self._require_admin(token_payload)
        return [
            AdminRoleDefinition(role=role, permissions=sorted(permissions))
            for role, permissions in sorted(ROLE_PERMISSIONS.items())
        ]

    async def admin_update_user(
        self,
        token_payload: dict,
        user_id: str,
        request: AdminUserUpdateRequest,
    ) -> UserProfile:
        self._require_admin(token_payload)
        user = await self.repository.get_user(user_id)
        if user is None:
            raise ServiceError(9004, "User not found")
        updates: dict[str, object] = {"updatedAt": now_ms()}
        if request.role is not None:
            if request.role not in ROLE_PERMISSIONS:
                raise ServiceError(9008, "Invalid role")
            updates["role"] = request.role
        if request.status is not None:
            if request.status not in {"active", "disabled"}:
                raise ServiceError(9009, "Invalid user status")
            updates["status"] = request.status
        if request.plan is not None:
            if request.plan not in PLANS:
                raise ServiceError(9006, "Invalid subscription plan")
            updates["plan"] = request.plan
            await self.repository.save_subscription(
                Subscription(
                    subscriptionId=self._id("sub", user.userId, request.plan, now_ms()),
                    userId=user.userId,
                    planId=request.plan,
                    status="active",
                    startedAt=now_ms(),
                )
            )
            await self.repository.save_usage(self._empty_usage(user.userId, request.plan, now_ms()))
        updated = model_copy_with_update(user, updates)
        await self.repository.save_user(updated)
        record_audit(
            str(token_payload["userId"]),
            "admin_update_user",
            user_id,
            "success",
            {
                "role": request.role or "",
                "status": request.status or "",
                "plan": request.plan or "",
            },
        )
        return self._profile(updated)

    async def create_api_key(
        self,
        user_id: str,
        request: ApiKeyCreateRequest,
    ) -> ApiKeyCreated:
        user = await self.repository.get_user(user_id)
        if user is None:
            raise ServiceError(9004, "User not found")
        self._validate_api_key_scopes(user.role, request.scopes)
        timestamp = now_ms()
        api_key, secret, secret_hash = generate_api_key()
        key_id = self._id("key", user_id, request.name, timestamp)
        stored = StoredApiKey(
            keyId=key_id,
            userId=user_id,
            name=request.name,
            apiKey=api_key,
            secretHash=secret_hash,
            scopes=request.scopes,
            status="active",
            createdAt=timestamp,
            updatedAt=timestamp,
        )
        await self.repository.save_api_key(stored)
        record_audit(user_id, "create_api_key", key_id, "success")
        return ApiKeyCreated(
            keyId=key_id,
            name=request.name,
            apiKey=api_key,
            secret=secret,
            scopes=request.scopes,
            status=stored.status,
            createdAt=timestamp,
        )

    async def list_api_keys(self, user_id: str) -> list[ApiKeyInfo]:
        await self.profile(user_id)
        return [self._api_key_info(row) for row in await self.repository.list_api_keys(user_id)]

    async def disable_api_key(self, user_id: str, key_id: str) -> ApiKeyInfo:
        row = await self.repository.get_api_key(key_id)
        if row is None or row.userId != user_id:
            raise ServiceError(9005, "API key not found")
        disabled = model_copy_with_update(row, {"status": "disabled", "updatedAt": now_ms()})
        await self.repository.save_api_key(disabled)
        record_audit(user_id, "disable_api_key", key_id, "success")
        return self._api_key_info(disabled)

    async def verify_api_key(self, api_key: str) -> ApiKeyVerification:
        key = await self.repository.get_api_key_by_value(api_key)
        if key is None or key.status != "active":
            raise ServiceError(1001, "Invalid API Key")
        user = await self.repository.get_user(key.userId)
        if user is None or user.status != "active":
            raise ServiceError(1001, "Invalid API Key")
        return ApiKeyVerification(
            keyId=key.keyId,
            userId=user.userId,
            role=user.role,
            plan=user.plan,
            scopes=key.scopes,
        )

    def plans(self) -> list[Plan]:
        return list(PLANS.values())

    async def subscription(self, user_id: str) -> Subscription:
        await self.profile(user_id)
        subscription = await self.repository.get_subscription(user_id)
        if subscription is None:
            raise ServiceError(9007, "Subscription not found")
        return subscription

    async def usage(self, user_id: str) -> UsageSummary:
        subscription = await self.subscription(user_id)
        summary = await self.repository.get_usage(user_id)
        if summary is None:
            summary = self._empty_usage(user_id, subscription.planId, now_ms())
            await self.repository.save_usage(summary)
        return summary

    async def record_usage(
        self,
        user_id: str,
        request: UsageRecordRequest,
    ) -> UsageSummary:
        summary = await self.usage(user_id)
        usage = dict(summary.usage)
        usage[request.metric] = usage.get(request.metric, 0) + request.amount
        updated = UsageSummary(
            userId=summary.userId,
            planId=summary.planId,
            periodStart=summary.periodStart,
            periodEnd=summary.periodEnd,
            requestLimit=summary.requestLimit,
            usage=usage,
            remainingRequests=max(0, summary.requestLimit - usage.get("api_requests", 0)),
        )
        await self.repository.save_usage(updated)
        return updated

    async def record_behavior(
        self,
        user_id: str,
        request: UserBehaviorEventRequest,
    ) -> UserBehaviorEvent:
        await self.profile(user_id)
        return await self._record_behavior(user_id, request.event, request.metadata)

    async def admin_operations(self, token_payload: dict, limit: int = 100) -> OperationsAnalytics:
        self._require_admin(token_payload)
        events = await self.repository.list_behavior_events(limit)
        counts: dict[str, int] = {}
        for event in events:
            counts[event.event] = counts.get(event.event, 0) + 1
        return OperationsAnalytics(
            totalEvents=len(events),
            activeUsers=len({event.userId for event in events}),
            eventCounts=counts,
            recentEvents=events,
        )

    def _profile(self, user: StoredUser) -> UserProfile:
        return UserProfile(
            userId=user.userId,
            email=user.email,
            role=user.role,
            plan=user.plan,
            status=user.status,
            createdAt=user.createdAt,
            updatedAt=user.updatedAt,
        )

    def _api_key_info(self, row: StoredApiKey) -> ApiKeyInfo:
        return ApiKeyInfo(
            keyId=row.keyId,
            userId=row.userId,
            name=row.name,
            apiKey=row.apiKey,
            scopes=row.scopes,
            status=row.status,
            createdAt=row.createdAt,
            updatedAt=row.updatedAt,
        )

    def _empty_usage(self, user_id: str, plan_id: str, timestamp: int) -> UsageSummary:
        plan = PLANS[plan_id]
        return UsageSummary(
            userId=user_id,
            planId=plan.planId,
            periodStart=timestamp,
            periodEnd=timestamp + 86_400_000,
            requestLimit=plan.requestLimitPerDay,
            usage={},
            remainingRequests=plan.requestLimitPerDay,
        )

    async def _record_behavior(
        self,
        user_id: str,
        event: str,
        metadata: dict[str, str],
    ) -> UserBehaviorEvent:
        record = UserBehaviorEvent(
            userId=user_id,
            event=event,
            timestamp=now_ms(),
            metadata=metadata,
        )
        await self.repository.save_behavior_event(record)
        return record

    @staticmethod
    def _id(prefix: str, *parts: object) -> str:
        raw = ":".join(str(part) for part in parts).encode()
        digest = hashlib.sha1(raw).hexdigest()[:12]
        return f"{prefix}_{digest}"

    def _role_for_email(self, email: str) -> str:
        return "admin" if email.lower() in get_settings().admin_email_set else "user"

    def _require_admin(self, token_payload: dict) -> None:
        if token_payload.get("role") != "admin":
            raise ServiceError(1004, "Admin permission required")

    @staticmethod
    def _validate_api_key_scopes(role: str, scopes: list[str]) -> None:
        permissions = ROLE_PERMISSIONS.get(role, set())
        if "*" in permissions:
            return
        invalid = [scope for scope in scopes if scope not in permissions]
        if invalid:
            raise ServiceError(1004, "API Key scope exceeds owner permission")
