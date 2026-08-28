# Kubernetes MVP Runbook

## Scope

This runbook covers the current Kubernetes manifests under
`deployment/k8s/base.yaml`. The MVP deploys application services and workers.
Redis, Kafka, ClickHouse, and MySQL are referenced as service endpoints and
should be provided by managed services, operators, or separate manifests.

## Included Resources

- Namespace
- ConfigMap
- Secret placeholder
- Deployments
- Services
- Ingress
- Readiness probes on `/ready`
- Liveness probes on `/health`
- Resource requests and limits

## Validate

```powershell
python scripts\validate_k8s_manifests.py
```

## Apply

```powershell
kubectl apply -f deployment/k8s/base.yaml
kubectl -n market-intelligence get pods
kubectl -n market-intelligence get svc
```

## Image

The manifests use:

```text
market-intelligence-service:latest
```

For production, replace this with a registry image tag produced by CI/CD.

## Required External Services

The ConfigMap expects:

- `redis`
- `kafka`
- `clickhouse`
- `mysql` for business persistence where applicable

## Remaining Work

- Helm chart or Kustomize overlays.
- Stateful infrastructure manifests or managed service integration.
- HorizontalPodAutoscaler.
- TLS ingress configuration.
- Secret management integration.
