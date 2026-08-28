# Logging MVP Runbook

## Scope

The current implementation emits JSON logs to stdout for every HTTP service.
This is the minimum shape required for Docker, Loki, ELK, or cloud log agents to
collect centralized logs.

## Log Format

Each request log contains:

- `timestamp`
- `level`
- `logger`
- `message`
- `service`
- `request_id`
- `method`
- `path`
- `status_code`
- `duration_ms`

Example:

```json
{"level":"INFO","logger":"mip.request","message":"http_request","service":"api-gateway","request_id":"...","method":"GET","path":"/ready","status_code":200,"duration_ms":1.2}
```

## Collection

For Docker Compose deployments, collect container stdout. Recommended labels and
pipelines can be added later for Loki or ELK.

## Local Verification

```powershell
python -m pytest backend\tests\test_logging.py
```

## Remaining Work

- Loki or ELK deployment manifests.
- Log retention policy enforcement.
- Correlation across async workers.
- Security log export and alert rules.
