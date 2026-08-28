from pydantic import BaseModel, Field


class NotificationMessage(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    body: str = Field(..., min_length=1, max_length=4000)
    severity: str = Field(default="info", min_length=2, max_length=20)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class NotificationSendRequest(BaseModel):
    channel: str = Field(default="console", min_length=3, max_length=30)
    userId: str = Field(default="default", min_length=1, max_length=64)
    target: str | None = Field(default=None, max_length=512)
    dedupeKey: str | None = Field(default=None, max_length=256)
    maxAttempts: int = Field(default=1, ge=1, le=5)
    message: NotificationMessage


class NotificationDelivery(BaseModel):
    deliveryId: str
    userId: str
    channel: str
    target: str | None
    dedupeKey: str | None = None
    title: str
    status: str
    error: str | None = None
    attempts: int = 0
    createdAt: int
    deliveredAt: int | None = None


class NotificationChannel(BaseModel):
    channel: str
    enabled: bool
    targetRequired: bool


class NotificationPreference(BaseModel):
    userId: str = Field(default="default", min_length=1, max_length=64)
    enabled: bool = True
    channels: list[str] = Field(default_factory=lambda: ["sse", "websocket"])
    minSeverity: str = "info"
    dedupeWindowSeconds: int = Field(default=300, ge=0, le=86400)
