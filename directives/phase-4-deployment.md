# Phase 4 — Scalable Deployment & API Hardening

**Weeks 13–16 | Status: 🔲 Not started**

## Goal
Move from "works on my machine" to production-ready: reliability, throughput, observability.

## Tasks
- [ ] Write K8s manifests: `infra/k8s/` — Deployments, HPA, Services, Ingress for api + worker
- [ ] HPA: scale worker on Redis queue depth metric (KEDA or custom metric adapter)
- [ ] Auth: JWT middleware on all non-health endpoints; API-key header support
- [ ] Rate limiting: `slowapi` (or nginx ingress annotations) — 100 req/min per key
- [ ] API versioning locked: all routes under `/v1/`; deprecation header for future `/v2/`
- [ ] OpenAPI spec export + Swagger sandbox at `/docs`
- [ ] Prometheus metrics: queue depth, diarization latency p95, RAG latency p95, error rate
- [ ] Grafana dashboard JSON in `infra/grafana/`
- [ ] Load test with Locust: 100 concurrent sessions, < 5% error rate, p95 < 3 s

## Kubernetes resource targets
| Service | Min replicas | Max replicas | Scale trigger |
|---------|-------------|-------------|---------------|
| api | 2 | 10 | CPU 70% |
| worker | 1 | 20 | Redis queue depth > 10 |

## Done criteria
- Deploy to GKE/EKS/AKS cluster; `kubectl get pods` all green
- Locust 100-user test: p95 latency < 3 s, error rate < 5%
- Grafana dashboard stays green under load

## Risks & mitigations
| Risk | Mitigation |
|------|-----------|
| pyannote model cold start (30-60 s) | Pre-load model at worker startup, not per-task |
| Secret sprawl in K8s | Use External Secrets Operator + AWS Secrets Manager / GCP Secret Manager |
| JWT secret rotation | Support multiple valid keys via JWKS endpoint |
