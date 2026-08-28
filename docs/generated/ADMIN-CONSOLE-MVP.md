# Admin Console MVP

## Source Selection

The admin console layout and permission-routing approach are adapted from:

- Repository: `vbenjs/vben-admin-thin-next`
- URL: `https://github.com/vbenjs/vben-admin-thin-next`
- License: MIT
- Stack: Vue 3, Vite, TypeScript

The project does not vendor the full template or its dependency tree. It uses
the same admin product structure: fixed application shell, admin side menu,
role-gated entry, summary cards, operational tables, and audit views.

## Implemented Scope

- Admin role gate in the main navigation.
- Admin dashboard page under the existing frontend.
- Admin snapshot API.
- User management table.
- User role, status, and plan update API.
- API key oversight table.
- Audit log view.
- RBAC role matrix.
- Operations panel for high-usage users and RBAC summary.
- `ADMIN_EMAILS` configuration for internal admin account assignment.

## API

- `GET /v1/admin/snapshot`
- `GET /v1/admin/users`
- `GET /v1/admin/api-keys`
- `GET /v1/admin/audit`
- `GET /v1/admin/roles`
- `POST /v1/admin/users/{user_id}`

The User Service validates that the bearer token contains `role=admin`.

## Local Admin Account

Set:

```powershell
$env:ADMIN_EMAILS="admin@example.com"
```

Register or login with `admin@example.com`; the generated profile has the
`admin` role and can open the Admin page.

## Validation

```powershell
python scripts\validate_admin_console.py
```

The validation is also run by `scripts/run_ci.py`.
