from pathlib import Path

REQUIRED_FILES = {
    "frontend/src/pages/AdminPage.vue",
    "frontend/src/api/admin.ts",
    "frontend/src/types/admin.ts",
    "docs/generated/ADMIN-CONSOLE-MVP.md",
    "backend/tests/test_user_api.py",
}

REQUIRED_FRONTEND_MARKERS = {
    "AdminPage",
    "'admin'",
    "visibleNavItems",
    "session.value?.profile.role === 'admin'",
}

REQUIRED_BACKEND_MARKERS = {
    "/v1/admin/snapshot",
    "/v1/admin/users",
    "/v1/admin/api-keys",
    "/v1/admin/audit",
    "/v1/admin/roles",
    "/v1/admin/users/{user_id}",
    "Admin permission required",
    "admin_update_user",
}


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in sorted(REQUIRED_FILES):
        if not (root / relative).is_file():
            errors.append(f"missing admin console file: {relative}")

    app_vue = (root / "frontend/src/App.vue").read_text(encoding="utf-8")
    for marker in sorted(REQUIRED_FRONTEND_MARKERS):
        if marker not in app_vue:
            errors.append(f"missing frontend admin marker: {marker}")

    user_main = (root / "backend/services/user_service/app/main.py").read_text(encoding="utf-8")
    user_services = (root / "backend/services/user_service/app/services.py").read_text(
        encoding="utf-8"
    )
    gateway = (root / "backend/services/api_gateway/app/main.py").read_text(encoding="utf-8")
    backend_text = "\n".join([user_main, user_services, gateway])
    for marker in sorted(REQUIRED_BACKEND_MARKERS):
        if marker not in backend_text:
            errors.append(f"missing backend admin marker: {marker}")

    checklist = (root / "docs/IMPLEMENTATION-GAP-CHECKLIST.md").read_text(encoding="utf-8")
    if "[x] Admin console MVP" not in checklist:
        errors.append("Admin console MVP is not checked in implementation checklist")

    admin_page = (root / "frontend/src/pages/AdminPage.vue").read_text(encoding="utf-8")
    for marker in ("updateAdminUser", "getAdminRoles", "role-matrix", "patchUser"):
        if marker not in admin_page:
            errors.append(f"missing admin user management marker: {marker}")

    runbook = (root / "docs/generated/ADMIN-CONSOLE-MVP.md").read_text(encoding="utf-8")
    if "vbenjs/vben-admin-thin-next" not in runbook or "MIT" not in runbook:
        errors.append("admin console runbook does not record GitHub source and license")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print("ok: admin console MVP contract is complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
