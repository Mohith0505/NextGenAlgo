# Infrastructure & DevOps Scaffolding

This directory contains the building blocks for local development, containerised deployment, and Kubernetes rollouts.

## Docker Compose Stack

The compose file now ships with supporting services for queues and monitoring:

```bash
cd infra
docker compose up --build
```

### Services
- `backend`: FastAPI API served by Uvicorn on port 8000.
- `worker`: Placeholder background worker sharing the backend image.
- `frontend`: Vite dev server exposed on port 5173.
- `db`: Postgres 16 with a persistent `db-data` volume.
- `redis`: Ephemeral cache / task queue backend.
- `prometheus` & `grafana`: Basic monitoring stack prewired for service discovery.

Prometheus scrapes the backend `/metrics` endpoint. Grafana auto provisions a Prometheus data source using the files under `monitoring/`.

## Kubernetes Manifests

`k8s/base` holds a minimal set of manifests to bootstrap a cluster namespace:
- Namespace, ConfigMap, and Secrets for environment wiring.
- Deployments for backend, worker, frontend, and Redis.
- Postgres StatefulSet with PVC template.
- Ingress resource templated for Traefik with TLS.

Apply the bundle with:

```bash
kubectl apply -f k8s/base
```

Replace placeholder container images and secrets with environment specific values before deploying.

## Observability Configuration

`monitoring/prometheus.yml` defines scrape targets for compose deployments.
`monitoring/grafana/datasources/datasource.yml` auto-registers Prometheus as the default data source.

## Next Steps
- Introduce IaC (Terraform/Pulumi) to provision cloud infrastructure.
- Wire GitHub Actions secrets and environment promotion gates.
- Expand monitoring dashboards and alerting rules once metrics are available.
