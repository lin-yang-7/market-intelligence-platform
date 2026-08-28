# Security Test MVP Runbook

## Scope

The MVP security suite validates the controls currently implemented in code:

- User login, token revocation, and password-change token invalidation.
- Gateway authentication header forwarding and permission checks.
- RBAC role and scope authorization.
- HMAC request signature validation and timestamp expiry.
- Fixed-window rate limiting.
- Audit log recording.
- Encrypted sensitive configuration loading.

## Run

```powershell
python scripts\security_test.py
```

Static-only configuration coverage check:

```powershell
python scripts\security_test.py --static-only
```

The local CI equivalent runs this suite automatically through:

```powershell
python scripts\run_ci.py
```

## Coverage Boundary

This MVP is code-level and configuration-level coverage. It does not replace
external dependency scanning, container image scanning, penetration testing, or
managed secret-store audits.

## Remaining Work

- Add dependency vulnerability scanning.
- Add container image scanning.
- Add API fuzzing and injection test cases.
- Add production secret-store access audit checks.
