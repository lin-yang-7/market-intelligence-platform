from pydantic import BaseModel, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    plan: str = Field(default="free", min_length=3, max_length=32)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email")
        return value.lower()


class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email")
        return value.lower()


class PasswordChangeRequest(BaseModel):
    oldPassword: str = Field(..., min_length=1, max_length=128)
    newPassword: str = Field(..., min_length=8, max_length=128)


class UserProfile(BaseModel):
    userId: str
    email: str
    role: str
    plan: str
    status: str
    createdAt: int
    updatedAt: int


class AuthToken(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    expiresIn: int
    profile: UserProfile


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    scopes: list[str] = Field(default_factory=lambda: ["market.read"])


class ApiKeyCreated(BaseModel):
    keyId: str
    name: str
    apiKey: str
    secret: str
    scopes: list[str]
    status: str
    createdAt: int


class ApiKeyInfo(BaseModel):
    keyId: str
    userId: str
    name: str
    apiKey: str
    scopes: list[str]
    status: str
    createdAt: int
    updatedAt: int


class ApiKeyVerification(BaseModel):
    keyId: str
    userId: str
    role: str
    plan: str
    scopes: list[str]


class Plan(BaseModel):
    planId: str
    name: str
    priceMonthly: float
    requestLimitPerDay: int
    features: list[str]


class Subscription(BaseModel):
    subscriptionId: str
    userId: str
    planId: str
    status: str
    startedAt: int
    renewsAt: int | None = None


class UsageRecordRequest(BaseModel):
    metric: str = Field(..., min_length=2, max_length=80)
    amount: int = Field(default=1, ge=1, le=1000000)


class UsageSummary(BaseModel):
    userId: str
    planId: str
    periodStart: int
    periodEnd: int
    requestLimit: int
    usage: dict[str, int]
    remainingRequests: int


class UserBehaviorEventRequest(BaseModel):
    event: str = Field(..., min_length=2, max_length=80)
    metadata: dict[str, str] = Field(default_factory=dict)


class UserBehaviorEvent(BaseModel):
    userId: str
    event: str
    timestamp: int
    metadata: dict[str, str] = Field(default_factory=dict)


class OperationsAnalytics(BaseModel):
    totalEvents: int
    activeUsers: int
    eventCounts: dict[str, int]
    recentEvents: list[UserBehaviorEvent]


class AdminSummaryMetric(BaseModel):
    label: str
    value: int | float | str
    tone: str = "neutral"


class AdminUserRow(BaseModel):
    profile: UserProfile
    subscription: Subscription | None = None
    usage: UsageSummary | None = None
    apiKeyCount: int = 0


class AdminSnapshot(BaseModel):
    metrics: list[AdminSummaryMetric]
    users: list[AdminUserRow]
    apiKeys: list[ApiKeyInfo]
    subscriptions: list[Subscription]
    usage: list[UsageSummary]
    auditEvents: list[dict[str, object]]


class AdminUserUpdateRequest(BaseModel):
    role: str | None = Field(default=None, min_length=3, max_length=32)
    status: str | None = Field(default=None, min_length=3, max_length=32)
    plan: str | None = Field(default=None, min_length=3, max_length=32)


class AdminRoleDefinition(BaseModel):
    role: str
    permissions: list[str]
