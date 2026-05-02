# Kubernetes manifests live here (Phase 4).
# Structure will be:
#   deployments/   — Deployment + HPA for api, worker
#   services/      — ClusterIP / LoadBalancer services
#   ingress/       — Nginx ingress with TLS
#   configmaps/    — Non-secret configuration
#   secrets/       — Secret manifests (sealed or external-secrets)
