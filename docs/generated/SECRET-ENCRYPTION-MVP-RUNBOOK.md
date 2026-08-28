# Secret Encryption MVP Runbook

## Scope

The platform supports encrypted environment variable values for sensitive
configuration. The MVP format is:

```text
enc:v1:<base64 payload>
```

Values are decrypted at configuration load time when
`SECRET_ENCRYPTION_KEY` is present.

## Supported Sensitive Variables

- `API_KEYS`
- `CLICKHOUSE_PASSWORD`
- `NOTIFICATION_WEBHOOK_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `SMTP_PASSWORD`
- `JWT_SECRET`

## Encrypt

```powershell
$env:PYTHONPATH="backend;backend/common"
$env:SECRET_ENCRYPTION_KEY="change-me"
python scripts\encrypt_secret.py --value "secret-value"
```

Use the printed `enc:v1:...` value in the matching environment variable.

## Production Guidance

This MVP avoids storing plaintext secrets in `.env` files and deployment
manifests. Production should still prefer Vault, KMS, Kubernetes External
Secrets, or cloud secret managers.

## Rotation

1. Generate a new encrypted value with the current `SECRET_ENCRYPTION_KEY`.
2. Update the environment variable or Kubernetes Secret.
3. Restart affected services.
4. Verify `/ready`.

## Remaining Work

- Managed secret store integration.
- Key rotation without restart.
- Secret access audit trail.
