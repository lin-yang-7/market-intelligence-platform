from fastapi.testclient import TestClient
from services.user_service.app.dependencies import get_user_service
from services.user_service.app.main import app
from services.user_service.app.repositories import InMemoryUserRepository
from services.user_service.app.services import UserService


def user_client() -> tuple[TestClient, UserService]:
    service = UserService(InMemoryUserRepository())
    app.dependency_overrides[get_user_service] = lambda: service
    return TestClient(app), service


def test_user_logout_revokes_token() -> None:
    client, _service = user_client()
    try:
        client.post(
            "/v1/user/register",
            json={"email": "demo@example.com", "password": "password123", "plan": "pro"},
        )
        login = client.post(
            "/v1/user/login",
            json={"email": "demo@example.com", "password": "password123"},
        )
        token = login.json()["data"]["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        profile = client.get("/v1/user/profile", headers=headers)
        logout = client.post("/v1/user/logout", headers=headers)
        revoked = client.get("/v1/user/profile", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert profile.status_code == 200
    assert logout.json()["data"] == {"status": "revoked"}
    assert revoked.status_code == 400
    assert revoked.json()["message"] == "Token revoked"


def test_change_password_revokes_current_token_and_allows_new_login() -> None:
    client, _service = user_client()
    try:
        client.post(
            "/v1/user/register",
            json={"email": "change@example.com", "password": "password123", "plan": "free"},
        )
        login = client.post(
            "/v1/user/login",
            json={"email": "change@example.com", "password": "password123"},
        )
        token = login.json()["data"]["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        changed = client.post(
            "/v1/user/password",
            json={"oldPassword": "password123", "newPassword": "newpassword123"},
            headers=headers,
        )
        old_profile = client.get("/v1/user/profile", headers=headers)
        old_login = client.post(
            "/v1/user/login",
            json={"email": "change@example.com", "password": "password123"},
        )
        new_login = client.post(
            "/v1/user/login",
            json={"email": "change@example.com", "password": "newpassword123"},
        )
    finally:
        app.dependency_overrides.clear()

    assert changed.json()["data"] == {"status": "password_changed"}
    assert old_profile.status_code == 400
    assert old_login.status_code == 400
    assert new_login.status_code == 200


def test_internal_api_key_verification_returns_scopes_and_rejects_invalid_key() -> None:
    client, _service = user_client()
    try:
        client.post(
            "/v1/user/register",
            json={"email": "key@example.com", "password": "password123", "plan": "pro"},
        )
        login = client.post(
            "/v1/user/login",
            json={"email": "key@example.com", "password": "password123"},
        )
        token = login.json()["data"]["accessToken"]
        created = client.post(
            "/v1/user/api-keys",
            json={"name": "sdk", "scopes": ["market.read", "rule.write"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        api_key = created.json()["data"]["apiKey"]
        verified = client.get(
            "/internal/api-keys/verify",
            headers={
                "X-API-Key": api_key,
                "X-Internal-Service-Token": "local-internal-service-token",
            },
        )
        invalid = client.get(
            "/internal/api-keys/verify",
            headers={
                "X-API-Key": "forged",
                "X-Internal-Service-Token": "local-internal-service-token",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert verified.status_code == 200
    assert verified.json()["data"]["scopes"] == ["market.read", "rule.write"]
    assert invalid.status_code == 400


def test_api_key_cannot_request_scope_outside_owner_permissions() -> None:
    client, _service = user_client()
    try:
        client.post(
            "/v1/user/register",
            json={"email": "scope@example.com", "password": "password123", "plan": "free"},
        )
        login = client.post(
            "/v1/user/login",
            json={"email": "scope@example.com", "password": "password123"},
        )
        denied = client.post(
            "/v1/user/api-keys",
            json={"name": "overreach", "scopes": ["admin.write"]},
            headers={"Authorization": f"Bearer {login.json()['data']['accessToken']}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert denied.status_code == 400
    assert denied.json()["message"] == "API Key scope exceeds owner permission"


def test_behavior_events_feed_admin_operations() -> None:
    from mip_common.config import get_settings

    client, _service = user_client()
    try:
        with __import__("pytest").MonkeyPatch.context() as monkeypatch:
            monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
            get_settings.cache_clear()
            client.post(
                "/v1/user/register",
                json={"email": "admin@example.com", "password": "password123", "plan": "pro"},
            )
            login = client.post(
                "/v1/user/login",
                json={"email": "admin@example.com", "password": "password123"},
            )
            headers = {"Authorization": f"Bearer {login.json()['data']['accessToken']}"}
            event = client.post(
                "/v1/user/events",
                json={"event": "dashboard_view", "metadata": {"page": "ranking"}},
                headers=headers,
            )
            operations = client.get("/v1/admin/operations", headers=headers)
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()

    assert event.status_code == 200
    assert operations.status_code == 200
    assert operations.json()["data"]["eventCounts"]["signup"] == 1
    assert operations.json()["data"]["eventCounts"]["dashboard_view"] == 1


def test_admin_snapshot_requires_admin_role(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
    from mip_common.config import get_settings

    get_settings.cache_clear()
    client, _service = user_client()
    try:
        client.post(
            "/v1/user/register",
            json={"email": "admin@example.com", "password": "password123", "plan": "pro"},
        )
        admin_login = client.post(
            "/v1/user/login",
            json={"email": "admin@example.com", "password": "password123"},
        )
        client.post(
            "/v1/user/register",
            json={"email": "user@example.com", "password": "password123", "plan": "free"},
        )
        user_login = client.post(
            "/v1/user/login",
            json={"email": "user@example.com", "password": "password123"},
        )

        admin_snapshot = client.get(
            "/v1/admin/snapshot",
            headers={"Authorization": f"Bearer {admin_login.json()['data']['accessToken']}"},
        )
        roles = client.get(
            "/v1/admin/roles",
            headers={"Authorization": f"Bearer {admin_login.json()['data']['accessToken']}"},
        )
        target_user_id = next(
            row["profile"]["userId"]
            for row in admin_snapshot.json()["data"]["users"]
            if row["profile"]["email"] == "user@example.com"
        )
        updated = client.post(
            f"/v1/admin/users/{target_user_id}",
            json={"role": "readonly", "status": "disabled", "plan": "pro"},
            headers={"Authorization": f"Bearer {admin_login.json()['data']['accessToken']}"},
        )
        denied = client.get(
            "/v1/admin/snapshot",
            headers={"Authorization": f"Bearer {user_login.json()['data']['accessToken']}"},
        )
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()

    assert admin_login.json()["data"]["profile"]["role"] == "admin"
    assert admin_snapshot.status_code == 200
    assert admin_snapshot.json()["data"]["metrics"]
    assert len(admin_snapshot.json()["data"]["users"]) == 2
    assert roles.status_code == 200
    assert roles.json()["data"][0]["role"] == "admin"
    assert updated.status_code == 200
    assert updated.json()["data"]["role"] == "readonly"
    assert updated.json()["data"]["status"] == "disabled"
    assert updated.json()["data"]["plan"] == "pro"
    assert denied.status_code == 400
    assert denied.json()["message"] == "Admin permission required"
