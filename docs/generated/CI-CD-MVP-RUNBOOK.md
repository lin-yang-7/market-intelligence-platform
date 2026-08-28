# CI/CD MVP Runbook

## Scope

This runbook documents the implemented CI path for the current repository. It
covers code checks, tests, frontend build, and Docker image build. Deployment
automation remains a future CD step.

## GitHub Actions

Workflow:

- `.github/workflows/ci.yml`

Triggers:

- Push to `main`
- Push to `develop`
- Pull request
- Manual `workflow_dispatch`

Jobs:

- Python checks: install dependencies, run Ruff, run pytest, import smoke, run
  disaster recovery readiness check, and validate Kubernetes manifests.
- Frontend build: `npm ci` and `npm run build`.
- Docker image build: build `backend/Dockerfile.service` without pushing.

## Local Equivalent

```powershell
python scripts\run_ci.py
```

This local script intentionally does not run Docker build, because local Docker
availability varies. Use this command when Docker is available:

```powershell
docker build -f backend/Dockerfile.service -t market-intelligence-service:ci .
```

## CD Workflow

Workflow:

- `.github/workflows/cd.yml`

Trigger:

- Manual `workflow_dispatch`

Pipeline:

- Validate release by running the local CI script.
- Build `backend/Dockerfile.service`.
- Push image to GHCR.
- Deploy over SSH using Docker Compose.
- Verify deployment through `scripts/check_deployment_health.py`.
- Print rollback instructions if deployment fails.

Required GitHub environment secrets:

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
- `DEPLOY_PATH`
- `DEPLOY_PORT` optional
- `DEPLOY_HEALTH_URL` optional

Production image override:

- `deployment/docker-compose.prod.yml`

Rollback:

- Re-run the CD workflow with a previous known-good `image_tag`.

## Remaining Work

- Security scan integration.
- Multi-environment promotion automation.
