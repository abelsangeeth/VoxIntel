# VoxIntel RAG

> Real-time conversational intelligence platform — audio ingestion, speaker diarization, domain-aware RAG, and analytics.

## Architecture

```
Input     │  Audio/Video  ·  Text/Docs  ·  External APIs (Zoom, Slack)
          │
Processing│  Speaker Diarization  ·  ASR Engine  ·  Multimodal Fusion
          │
Intelligence│ Domain RAG  ·  LLM Core  ·  Analytics Engine
          │
Deployment│  Docker/K8s  ·  Async Queue  ·  REST/WS API
```

## Monorepo Layout

```
apps/
  api/        FastAPI — REST + WebSocket + SSE endpoints
  worker/     Async worker — diarization, RAG, analytics tasks
packages/
  shared/     Pydantic schemas, utilities shared across apps
migrations/   Alembic database migrations
infra/
  k8s/        Kubernetes manifests (Phase 4)
.github/
  workflows/  CI/CD pipelines
```

## Quick Start

```bash
# 1. Copy env and fill in secrets
cp .env.example .env

# 2. Start all services
docker compose up --build

# 3. Check health
curl http://localhost:8000/v1/health
```

## Phases

| Phase | Scope | Weeks |
|-------|-------|-------|
| 0 | Foundation & Scaffolding | 1–2 |
| 1 | Audio Ingestion & Speaker Diarization | 3–5 |
| 2 | Domain-Aware RAG Pipeline | 6–9 |
| 3 | Conversation Analytics | 10–12 |
| 4 | Scalable Deployment & API Hardening | 13–16 |
| 5 | Integrations & Polish | 17–20 |

## Requirements

- Docker ≥ 24 + Docker Compose v2
- Python 3.11+
- Node.js 20+ (optional, for tooling scripts)
