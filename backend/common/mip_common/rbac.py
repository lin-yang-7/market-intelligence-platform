from dataclasses import dataclass

from fastapi import Request

from .auth import get_api_identity
from .responses import ServiceError

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"*"},
    "user": {
        "market.read",
        "feature.read",
        "ranking.read",
        "screener.read",
        "signal.read",
        "alert.read",
        "alert.write",
        "notification.read",
        "notification.write",
        "history.read",
        "score.read",
        "rule.read",
        "rule.write",
        "feature_store.read",
        "user.read",
        "user.write",
        "api_key.write",
        "billing.read",
    },
    "readonly": {
        "market.read",
        "feature.read",
        "ranking.read",
        "screener.read",
        "signal.read",
        "history.read",
        "score.read",
        "feature_store.read",
    },
    "api_key": set(),
}


@dataclass(frozen=True)
class PermissionIdentity:
    principal: str
    role: str
    scopes: set[str]
    authenticated: bool


def has_permission(identity: PermissionIdentity, permission: str) -> bool:
    if "*" in identity.scopes:
        return True
    if permission in identity.scopes:
        return True
    if any(_wildcard_match(scope, permission) for scope in identity.scopes):
        return True
    role_permissions = ROLE_PERMISSIONS.get(identity.role, set())
    return "*" in role_permissions or permission in role_permissions


def require_permission(identity: PermissionIdentity, permission: str) -> None:
    if not identity.authenticated:
        raise ServiceError(1001, "Authentication required")
    if not has_permission(identity, permission):
        raise ServiceError(1004, "Permission denied")


def identity_from_request(request: Request) -> PermissionIdentity:
    identity = get_api_identity(request)
    return PermissionIdentity(
        principal=identity.principal,
        role=identity.role,
        scopes=set(identity.scopes),
        authenticated=identity.authenticated,
    )


def require_request_permission(request: Request, permission: str) -> None:
    require_permission(identity_from_request(request), permission)


def _wildcard_match(scope: str, permission: str) -> bool:
    if not scope.endswith(".*"):
        return False
    return permission.startswith(scope[:-1])
