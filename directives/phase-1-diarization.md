# Phase 1 — Audio Ingestion & Speaker Diarization

**Weeks 3–5 | Status: 🔲 Not started**

## Goal
Build the front-end of the pipeline: audio in → diarized + transcribed utterances in the DB.

## Tasks
- [ ] Integrate `pyannote/speaker-diarization-3.1` via `diarization.run` Celery task
- [ ] Integrate `faster-whisper` (base model) for per-segment transcription
- [ ] Wire `POST /v1/sessions/{id}/audio` → Redis queue → worker → DB
- [ ] Implement SSE stream at `GET /v1/sessions/{id}/transcript/stream`
- [ ] Accept optional `.txt`/`.pdf` context document alongside audio upload
- [ ] Write integration test: upload a 2-speaker WAV, assert utterances in DB

## Architecture
```
POST /sessions/{id}/audio
        │
        ▼
  Redis Stream "audio_jobs"
        │
        ▼
  Worker: diarization.run
        │  (segments with speaker labels)
        ▼
  Worker: transcription.run_segment  ×N  (parallel per segment)
        │
        ▼
  DB: speakers + utterances rows
        │
        ▼
  SSE stream pushes new utterances to client
```

## Done criteria
- Upload a 2-person audio file → `[Speaker A]: "..." / [Speaker B]: "..."` in DB within ≤10 s
- SSE stream delivers utterances in real time (latency ≤ 2 s per chunk)
- Worker retries on transient failure without losing the job

## Risks & mitigations
| Risk | Mitigation |
|------|-----------|
| GPU memory (pyannote is heavy) | Use `cpu` device in dev; GPU in prod K8s node |
| Audio format variety (MP4, WebM, M4A) | Use ffmpeg to transcode to WAV before diarization |
| HuggingFace rate limits | Cache model weights in a Docker volume |
