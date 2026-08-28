import pytest
from mip_common.rbac import PermissionIdentity, has_permission, require_permission
from mip_common.responses import ServiceError


def test_admin_has_all_permissions() -> None:
    identity = PermissionIdentity("usr_admin", "admin", set(), True)

    assert has_permission(identity, "billing.write")


def test_scope_grants_permission_and_wildcard_scope() -> None:
    identity = PermissionIdentity("key", "readonly", {"rule.*"}, True)

    assert has_permission(identity, "rule.write")
    assert not has_permission(identity, "billing.write")


def test_role_grants_default_permissions() -> None:
    identity = PermissionIdentity("usr", "user", set(), True)

    assert has_permission(identity, "rule.write")
    assert not has_permission(identity, "billing.write")


def test_require_permission_rejects_anonymous_and_denied() -> None:
    with pytest.raises(ServiceError) as anonymous:
        require_permission(PermissionIdentity("anon", "anonymous", set(), False), "market.read")
    with pytest.raises(ServiceError) as denied:
        require_permission(PermissionIdentity("usr", "readonly", set(), True), "rule.write")

    assert anonymous.value.code == 1001
    assert denied.value.code == 1004
