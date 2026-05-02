# execution/

Deterministic scripts and runbooks delegated by the agent.

## Quick-reference commands

```bash
# Start local stack
docker compose up --build

# Start with observability (Prometheus + Grafana)
docker compose --profile observability up --build

# Apply DB migrations
alembic upgrade head

# Roll back last migration
alembic downgrade -1

# Run all tests
pytest

# Lint + format
ruff check . && ruff format --check .

# Celery worker (local, no Docker)
celery -A apps.worker.app.main worker --loglevel=info --concurrency=2

# Load test (Phase 4)
locust -f execution/locustfile.py --host=http://localhost:8000
```
