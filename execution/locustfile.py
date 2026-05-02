"""
Locust load test — Phase 4.

Target: 100 concurrent sessions without degradation.

Usage:
  locust -f execution/locustfile.py --host http://localhost:8000 \
         -u 100 -r 10 --run-time 5m --headless

Scenarios:
  1. CreateSession   — POST /v1/sessions
  2. GetSession      — GET  /v1/sessions/{id}
  3. RAGQuery        — POST /v1/sessions/{id}/rag?question=...
  4. IngestDocument  — POST /v1/documents
  5. GetHealth       — GET  /v1/health  (baseline)
"""

import random
import uuid

from locust import HttpUser, between, task

# ── Auth token ────────────────────────────────────────────────────────────────
# Obtain once; all virtual users share it for simplicity.
_SHARED_TOKEN: str | None = None


def _get_token(client) -> str:
    global _SHARED_TOKEN
    if _SHARED_TOKEN is None:
        resp = client.post(
            "/v1/auth/token",
            json={"username": "demo", "password": "voxintel-demo"},
            name="auth/token",
        )
        if resp.status_code == 200:
            _SHARED_TOKEN = resp.json()["access_token"]
        else:
            _SHARED_TOKEN = "invalid"
    return _SHARED_TOKEN


class VoxIntelUser(HttpUser):
    """Simulates a real API consumer across the full session lifecycle."""

    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        token = _get_token(self.client)
        self.client.headers.update({"Authorization": f"Bearer {token}"})
        self.session_id: str | None = None

    # ── Weighted tasks ────────────────────────────────────────────────────────

    @task(3)
    def health_check(self) -> None:
        self.client.get("/v1/health", name="health")

    @task(5)
    def create_session(self) -> None:
        resp = self.client.post(
            "/v1/sessions",
            json={
                "title": f"Load Test Session {uuid.uuid4().hex[:8]}",
                "source": "locust",
            },
            name="sessions/create",
        )
        if resp.status_code == 201:
            self.session_id = resp.json()["id"]

    @task(8)
    def get_session(self) -> None:
        if not self.session_id:
            return
        self.client.get(f"/v1/sessions/{self.session_id}", name="sessions/get")

    @task(4)
    def list_utterances(self) -> None:
        if not self.session_id:
            return
        self.client.get(
            f"/v1/sessions/{self.session_id}/utterances?limit=50",
            name="sessions/utterances",
        )

    @task(2)
    def rag_query(self) -> None:
        if not self.session_id:
            return
        questions = [
            "What are the main action items?",
            "Who was responsible for the budget review?",
            "What did the contract say about liability?",
            "Summarise the key decisions made.",
        ]
        self.client.post(
            f"/v1/sessions/{self.session_id}/rag",
            params={"question": random.choice(questions)},
            name="sessions/rag",
        )

    @task(1)
    def export_json(self) -> None:
        if not self.session_id:
            return
        self.client.get(
            f"/v1/sessions/{self.session_id}/export?format=json",
            name="sessions/export",
        )

    @task(2)
    def ingest_document(self) -> None:
        sample_text = (
            b"This is a sample contract document for load testing purposes. "
            b"Liability clause: the vendor is not responsible for indirect damages. "
            b"Payment terms: net 30 days."
        )
        self.client.post(
            "/v1/documents",
            files={"file": ("sample.txt", sample_text, "text/plain")},
            name="documents/ingest",
        )
