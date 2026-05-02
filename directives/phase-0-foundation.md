# Phase 0 — Foundation & Scaffolding

**Weeks 1–2 | Status: ✅ Scaffolded**

## Goal
Stand up the monorepo skeleton, data contracts, and local dev stack before writing any feature code.

## Deliverables
- [x] Monorepo layout: `apps/api`, `apps/worker`, `packages/shared`
- [x] `docker-compose.yml` — PostgreSQL 16, Redis 7, Qdrant, API, Worker, Prometheus/Grafana (observability profile)
- [x] FastAPI skeleton with `/v1/health` endpoint
- [x] Alembic migration `001` — conversations, speakers, utterances, documents, document_chunks, session_summaries
- [x] GitHub Actions CI — lint → test-api → test-worker → docker-build
- [x] `.env.example` with all required keys documented

## Key design decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| API framework | FastAPI + asyncpg | Async-native, OpenAPI built-in |
| Task queue | Celery + Redis | Simple, battle-tested, easy to scale workers |
| Vector store | Qdrant | Self-hosted, fast cosine search, free tier |
| DB | PostgreSQL + JSONB | Structured + schema-flexible metadata |
| Embeddings | `text-embedding-3-small` | Cost-efficient, 1536-dim |

## Done criteria
- `docker compose up` boots all services with no errors
- `GET /v1/health` returns `{"status": "ok"}`
- `alembic upgrade head` applies migration without error
- CI pipeline passes on a clean branch

## Risks
- `pyannote.audio` requires HuggingFace token and accepts license — complete before Phase 1
- OpenAI API key budget — set a spending limit before Phase 2
